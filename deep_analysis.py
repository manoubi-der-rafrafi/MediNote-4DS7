"""
Medinote — Deep Business Intelligence Engine
Extracts comprehensive insights from all available CRM tables.

Usage:
    python deep_analysis.py
"""

import json
import logging
import os
import sys
from datetime import datetime

import pandas as pd
from sqlalchemy import text

sys.path.insert(0, r"c:\Users\omri\Desktop\pii")
from db_layer import MedinoteDB

log = logging.getLogger("medinote.deep")

REFERENCE_DATE = "2026-01-22"
REPORTS_DIR    = r"c:\Users\omri\Desktop\pii\reports"

# ─── small helper so every section is failure-safe ────────────────────────────

def _safe(fn, label="section"):
    try:
        return fn()
    except Exception as exc:
        log.warning("Deep analysis section '%s' failed: %s", label, exc)
        return {}


# =============================================================================
# MAIN ENGINE
# =============================================================================

class DeepAnalysis:
    def __init__(self, db: MedinoteDB):
        self.db  = db
        self.ref = REFERENCE_DATE
        # 120-second per-query hard limit (MariaDB)
        try:
            db.execute(text("SET SESSION max_statement_time=120"))
        except Exception:
            pass

    # ── query wrapper ─────────────────────────────────────────────────────────

    def _q(self, sql: str, params: dict | None = None) -> pd.DataFrame:
        return self.db.query(text(sql), params or {})

    def run_all(self) -> dict:
        print("Running deep analysis…\n")
        return {
            "geographic": _safe(self.geographic_analysis,  "geographic"),
            "delegates":  _safe(self.delegate_analysis,    "delegates"),
            "products":   _safe(self.product_analysis,     "products"),
            "pharmacies": _safe(self.pharmacy_analysis,    "pharmacies"),
            "temporal":   _safe(self.temporal_analysis,    "temporal"),
            "animations": _safe(self.animation_analysis,   "animations"),
            "rfm":        _safe(self.rfm_analysis,         "rfm"),
            "objectives": _safe(self.objectives_analysis,  "objectives"),
        }

    # =========================================================================
    # SECTION 1 — GEOGRAPHIC
    # =========================================================================

    def geographic_analysis(self) -> dict:
        print("  [1/8] Geographic analysis…")

        revenue_by_zone = self._q("""
            SELECT zone,
                   SUM(ttc)                       AS total_revenue,
                   COUNT(DISTINCT cl)             AS pharmacy_count,
                   COUNT(DISTINCT dlg)            AS delegate_count,
                   SUM(ttc)/COUNT(DISTINCT cl)    AS revenue_per_pharmacy
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(date) >= DATE_SUB(:ref, INTERVAL 12 MONTH)
              AND  zone IS NOT NULL AND zone != ''
            GROUP  BY zone
            ORDER  BY total_revenue DESC
        """, {"ref": self.ref})

        # t_gouv_id_del_id_nom actual columns: del_id, nom (small table — fast)
        gouv_map = self._q("SELECT del_id, nom FROM t_gouv_id_del_id_nom")

        # delegate revenue for gouv aggregation (pre-aggregated, no JOIN on big table)
        del_rev_gouv = self._q("""
            SELECT dlg, SUM(ttc) AS total_revenue, COUNT(DISTINCT cl) AS pharmacy_count
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(date) >= DATE_SUB(:ref, INTERVAL 12 MONTH)
              AND  dlg IS NOT NULL AND dlg != ''
            GROUP  BY dlg
        """, {"ref": self.ref})

        # merge in Python — no heavy JOIN in SQL
        revenue_by_gouv = pd.DataFrame()
        if len(gouv_map) and len(del_rev_gouv):
            gouv_map["del_id"] = gouv_map["del_id"].astype(str)
            del_rev_gouv["dlg"] = del_rev_gouv["dlg"].astype(str)
            merged = del_rev_gouv.merge(gouv_map, left_on="dlg", right_on="del_id", how="left")
            merged["nom"] = merged["nom"].fillna("Unknown")
            revenue_by_gouv = (
                merged.groupby("nom")
                .agg(total_revenue=("total_revenue", "sum"),
                     pharmacy_count=("pharmacy_count", "sum"),
                     delegate_count=("dlg", "nunique"))
                .reset_index()
                .rename(columns={"nom": "nom_gouv"})
                .sort_values("total_revenue", ascending=False)
            )

        dead_zones = self._q("""
            SELECT zone
            FROM (
                SELECT zone, MAX(DATE(date)) AS last_sale
                FROM   t_ttc_ht_qte_qte_g
                WHERE  zone IS NOT NULL AND zone != ''
                  AND  DATE(date) >= DATE_SUB(:ref, INTERVAL 12 MONTH)
                GROUP  BY zone
            ) z
            WHERE last_sale < DATE_SUB(:ref, INTERVAL 90 DAY)
        """, {"ref": self.ref})

        coverage_gaps = self._q("""
            SELECT zone,
                   COUNT(DISTINCT cl)  AS pharmacies,
                   COUNT(DISTINCT dlg) AS delegates,
                   SUM(ttc)            AS revenue
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(date) >= DATE_SUB(:ref, INTERVAL 12 MONTH)
            GROUP  BY zone
            HAVING delegates = 0 OR delegates IS NULL
        """, {"ref": self.ref})

        # Zone weight table (t_nom_zone_poids_gouv: nom, zone, poids, gouv)
        zone_weights = self._q("SELECT nom, zone, poids, gouv FROM t_nom_zone_poids_gouv")

        return {
            "revenue_by_zone":  revenue_by_zone.to_dict("records"),
            "revenue_by_gouv":  revenue_by_gouv.to_dict("records"),
            "dead_zones":       dead_zones["zone"].tolist() if len(dead_zones) else [],
            "top_zone":         revenue_by_zone.iloc[0].to_dict() if len(revenue_by_zone) else {},
            "bottom_zone":      revenue_by_zone.iloc[-1].to_dict() if len(revenue_by_zone) else {},
            "coverage_gaps":    coverage_gaps.to_dict("records"),
            "zone_weights":     zone_weights.to_dict("records"),
        }

    # =========================================================================
    # SECTION 2 — DELEGATES
    # =========================================================================

    def delegate_analysis(self) -> dict:
        print("  [2/8] Delegate analysis…")

        delegate_perf = self._q("""
            SELECT s.dlg,
                   SUM(s.ttc)                                           AS revenue_12m,
                   SUM(CASE WHEN DATE(s.date) >= DATE_SUB(:ref, INTERVAL 3 MONTH)
                            THEN s.ttc ELSE 0 END)                      AS revenue_3m,
                   SUM(CASE WHEN DATE(s.date) >= DATE_SUB(:ref, INTERVAL 1 MONTH)
                            THEN s.ttc ELSE 0 END)                      AS revenue_1m,
                   COUNT(DISTINCT s.cl)                                 AS pharmacies_covered,
                   COUNT(DISTINCT DATE(s.date))                         AS active_days,
                   COUNT(DISTINCT s.art)                                AS products_sold
            FROM   t_ttc_ht_qte_qte_g s
            WHERE  s.dlg IS NOT NULL AND s.dlg != ''
              AND  DATE(s.date) >= DATE_SUB(:ref, INTERVAL 12 MONTH)
            GROUP  BY s.dlg
            ORDER  BY revenue_12m DESC
        """, {"ref": self.ref})

        # CA objectives: id_del, caph, cagro, obj, year
        del_obj = self._q("SELECT * FROM t_id_del_caph_cagro_obj LIMIT 500")

        # Visit planning: idDel (not iddel)
        visit_plan = self._q("""
            SELECT idDel                       AS delegate_id,
                   COUNT(*)                    AS planned_visits,
                   COUNT(DISTINCT jour)        AS visit_days,
                   COUNT(DISTINCT secteur)     AS sectors_covered
            FROM   t_secteur_iddel_jour_date_creation
            GROUP  BY idDel
            ORDER  BY planned_visits DESC
        """)

        # Pharmacy-delegate assignments
        ph_dlg = self._q("SELECT cl, dlg FROM t_cl_dlg LIMIT 10000")

        top_delegate     = None
        avg_revenue      = 0.0
        below_avg        = pd.DataFrame()

        if len(delegate_perf):
            delegate_perf["efficiency"] = (
                delegate_perf["revenue_12m"] /
                delegate_perf["pharmacies_covered"].clip(lower=1)
            )
            top_delegate = str(delegate_perf.iloc[0]["dlg"])
            avg_revenue  = float(delegate_perf["revenue_12m"].mean())
            below_avg    = delegate_perf[delegate_perf["revenue_12m"] < avg_revenue]

        return {
            "delegate_performance":     delegate_perf.to_dict("records"),
            "top_delegate":             top_delegate,
            "avg_revenue_12m":          round(avg_revenue, 2),
            "below_average_count":      len(below_avg),
            "below_average_delegates":  below_avg["dlg"].tolist() if len(below_avg) else [],
            "ca_objectives":            del_obj.to_dict("records"),
            "visit_planning":           visit_plan.to_dict("records"),
            "pharmacy_delegate_map":    ph_dlg.to_dict("records"),
        }

    # =========================================================================
    # SECTION 3 — PRODUCTS
    # =========================================================================

    def product_analysis(self) -> dict:
        print("  [3/8] Product analysis…")

        top_products = self._q("""
            SELECT art,
                   fam,
                   SUM(ttc)           AS revenue_12m,
                   SUM(qte)           AS qty_12m,
                   COUNT(DISTINCT cl) AS buyer_count,
                   COUNT(DISTINCT dlg)AS delegate_count
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(date) >= DATE_SUB(:ref, INTERVAL 12 MONTH)
            GROUP  BY art, fam
            ORDER  BY revenue_12m DESC
            LIMIT  50
        """, {"ref": self.ref})

        family_perf = self._q("""
            SELECT fam,
                   SUM(ttc)            AS revenue_12m,
                   SUM(qte)            AS qty_12m,
                   COUNT(DISTINCT art) AS product_count,
                   COUNT(DISTINCT cl)  AS buyer_count
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(date) >= DATE_SUB(:ref, INTERVAL 12 MONTH)
              AND  fam IS NOT NULL AND fam != ''
            GROUP  BY fam
            ORDER  BY revenue_12m DESC
        """, {"ref": self.ref})

        product_trend = self._q("""
            SELECT art,
                   SUM(CASE WHEN DATE(date) >= DATE_SUB(:ref, INTERVAL 3 MONTH)
                            THEN ttc ELSE 0 END)                         AS rev_3m,
                   SUM(CASE WHEN DATE(date) BETWEEN
                                DATE_SUB(:ref, INTERVAL 6 MONTH)
                            AND DATE_SUB(:ref, INTERVAL 3 MONTH)
                            THEN ttc ELSE 0 END)                         AS rev_prev_3m
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(date) >= DATE_SUB(:ref, INTERVAL 6 MONTH)
            GROUP  BY art
            HAVING rev_3m > 0 OR rev_prev_3m > 0
        """, {"ref": self.ref})

        product_by_zone = self._q("""
            SELECT art, zone, SUM(ttc) AS revenue
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(date) >= DATE_SUB(:ref, INTERVAL 6 MONTH)
              AND  zone IS NOT NULL AND zone != ''
            GROUP  BY art, zone
            ORDER  BY revenue DESC
            LIMIT  100
        """, {"ref": self.ref})

        # Product catalog: code_article, titre, famille, pvttc
        catalog = self._q("""
            SELECT code_article, titre, famille, pvttc, dispo, etat
            FROM   t_bare_code_code_article_titre_description
            WHERE  etat = 1 OR etat IS NULL
            ORDER  BY pvttc DESC
        """)

        # Year/sector breakdown
        yearly_by_sector = self._q("""
            SELECT article, year, secteur, SUM(ca) AS ca, SUM(qte) AS qte
            FROM   t_article_year_secteur_ca_2
            WHERE  year >= 2022
            GROUP  BY article, year, secteur
            ORDER  BY year DESC, ca DESC
            LIMIT  200
        """)

        # Family names from t_nom_5
        families = self._q("SELECT id, nom FROM t_nom_5")

        growing  = pd.DataFrame()
        declining = pd.DataFrame()
        if len(product_trend):
            product_trend["trend_pct"] = (
                (product_trend["rev_3m"] - product_trend["rev_prev_3m"]) /
                product_trend["rev_prev_3m"].clip(lower=1) * 100
            )
            growing   = product_trend[product_trend["trend_pct"] > 10]
            declining = product_trend[product_trend["trend_pct"] < -10]

        return {
            "top_products":          top_products.to_dict("records"),
            "family_performance":    family_perf.to_dict("records"),
            "growing_products":      growing["art"].tolist()   if len(growing)   else [],
            "declining_products":    declining["art"].tolist() if len(declining) else [],
            "product_by_zone":       product_by_zone.to_dict("records"),
            "catalog":               catalog.to_dict("records"),
            "yearly_by_sector":      yearly_by_sector.to_dict("records"),
            "family_names":          families.to_dict("records"),
            "total_active_products": len(top_products),
            "growing_count":         len(growing),
            "declining_count":       len(declining),
        }

    # =========================================================================
    # SECTION 4 — PHARMACIES
    # =========================================================================

    def pharmacy_analysis(self) -> dict:
        print("  [4/8] Pharmacy analysis…")

        pharmacy_profile = self._q("""
            SELECT cl,
                   zone,
                   SUM(ttc)                                              AS revenue_total,
                   COUNT(DISTINCT DATE(date))                            AS order_days,
                   MAX(DATE(date))                                       AS last_order_date,
                   DATEDIFF(:ref, MAX(DATE(date)))                       AS days_inactive,
                   SUM(CASE WHEN DATE(date) >= DATE_SUB(:ref, INTERVAL 3 MONTH)
                            THEN ttc ELSE 0 END)                         AS revenue_3m,
                   SUM(CASE WHEN DATE(date) BETWEEN
                                DATE_SUB(:ref, INTERVAL 6 MONTH)
                            AND DATE_SUB(:ref, INTERVAL 3 MONTH)
                            THEN ttc ELSE 0 END)                         AS revenue_prev_3m
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(date) >= DATE_SUB(:ref, INTERVAL 12 MONTH)
            GROUP  BY cl, zone
        """, {"ref": self.ref})

        # Pharmacy CRM profiles (potential, spec, gouvernorat)
        crm_profiles = self._q("""
            SELECT id_pros AS cl, nom, prenom, potentiel,
                   gouvernorat, delegation, activite
            FROM   t_id_pros_nom_prenom_potentiel
            LIMIT  5000
        """)

        # Pending orders
        orders = self._q("""
            SELECT etat, COUNT(*) AS count, label
            FROM   t_demande_id_type_pay_label_etat
            GROUP  BY etat, label
            ORDER  BY count DESC
        """)

        segments      = {}
        top_pharmacies = pd.DataFrame()
        fast_growing  = pd.DataFrame()

        if len(pharmacy_profile):
            pharmacy_profile["segment"] = "ACTIVE"
            pharmacy_profile.loc[pharmacy_profile["days_inactive"] > 240, "segment"] = "CHURNED"
            pharmacy_profile.loc[pharmacy_profile["days_inactive"].between(90, 240), "segment"] = "AT_RISK"
            pharmacy_profile.loc[pharmacy_profile["days_inactive"].between(30, 90),  "segment"] = "COOLING"

            segments       = pharmacy_profile["segment"].value_counts().to_dict()
            top_pharmacies = pharmacy_profile.nlargest(20, "revenue_total")

            pharmacy_profile["growth_pct"] = (
                (pharmacy_profile["revenue_3m"] - pharmacy_profile["revenue_prev_3m"]) /
                pharmacy_profile["revenue_prev_3m"].clip(lower=1) * 100
            )
            fast_growing = pharmacy_profile[pharmacy_profile["growth_pct"] > 50]

        top_cols = ["cl", "zone", "revenue_total", "order_days", "days_inactive", "segment"]

        return {
            "total_pharmacies":  len(pharmacy_profile),
            "segments":          segments,
            "top_pharmacies":    top_pharmacies[top_cols].to_dict("records") if len(top_pharmacies) else [],
            "fast_growing":      fast_growing["cl"].tolist() if len(fast_growing) else [],
            "fast_growing_count":len(fast_growing),
            "crm_profiles":      crm_profiles.to_dict("records"),
            "order_status":      orders.to_dict("records"),
        }

    # =========================================================================
    # SECTION 5 — TEMPORAL
    # =========================================================================

    def temporal_analysis(self) -> dict:
        print("  [5/8] Temporal analysis…")

        monthly_trend = self._q("""
            SELECT DATE_FORMAT(date, '%Y-%m') AS month,
                   SUM(ttc)                   AS revenue,
                   COUNT(DISTINCT cl)         AS active_pharmacies,
                   COUNT(DISTINCT dlg)        AS active_delegates
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(date) >= DATE_SUB(:ref, INTERVAL 24 MONTH)
            GROUP  BY DATE_FORMAT(date, '%Y-%m')
            ORDER  BY month
        """, {"ref": self.ref})

        # derive yearly from monthly_trend — avoids a second full-table scan
        if len(monthly_trend):
            monthly_trend["_year"] = monthly_trend["month"].str[:4].astype(int)
            yearly = (
                monthly_trend.groupby("_year")
                .agg(revenue=("revenue", "sum"),
                     pharmacies=("active_pharmacies", "max"))
                .reset_index()
                .rename(columns={"_year": "year"})
                .sort_values("year")
            )
        else:
            yearly = pd.DataFrame(columns=["year", "revenue", "pharmacies"])

        # derive seasonality from monthly_trend — same data, no extra query
        if len(monthly_trend):
            monthly_trend["_month_num"] = monthly_trend["month"].str[5:7].astype(int)
            seasonality = (
                monthly_trend.groupby("_month_num")
                .agg(avg_revenue=("revenue", "mean"))
                .reset_index()
                .rename(columns={"_month_num": "month_num"})
                .sort_values("avg_revenue", ascending=False)
            )
        else:
            seasonality = pd.DataFrame(columns=["month_num", "avg_revenue"])

        # YoY growth from yearly data
        yoy_growth = None
        if len(yearly) >= 2:
            rev_curr = float(yearly.iloc[-1]["revenue"])
            rev_prev = float(yearly.iloc[-2]["revenue"])
            if rev_prev > 0:
                yoy_growth = round((rev_curr - rev_prev) / rev_prev * 100, 2)

        return {
            "monthly_trend":      monthly_trend.to_dict("records"),
            "yearly_comparison":  yearly.to_dict("records"),
            "seasonality":        seasonality.to_dict("records"),
            "best_month":         int(seasonality.iloc[0]["month_num"])  if len(seasonality) else None,
            "worst_month":        int(seasonality.iloc[-1]["month_num"]) if len(seasonality) else None,
            "yoy_growth_pct":     yoy_growth,
        }

    # =========================================================================
    # SECTION 6 — ANIMATIONS
    # =========================================================================

    def animation_analysis(self) -> dict:
        print("  [6/8] Animation analysis…")

        # Column is id_pharmay (not id_pharmacy)
        animation_summary = self._q("""
            SELECT etat, COUNT(*) AS count
            FROM   t_id_pharmay_id_annimatrice_date_annimation_etat
            GROUP  BY etat
            ORDER  BY count DESC
        """)

        anim_per_pharmacy = self._q("""
            SELECT id_pharmay                                       AS pharmacy_id,
                   COUNT(*)                                         AS animation_count,
                   SUM(CASE WHEN etat = 1 THEN 1 ELSE 0 END)       AS completed,
                   MAX(date_annimation)                             AS last_animation
            FROM   t_id_pharmay_id_annimatrice_date_annimation_etat
            GROUP  BY id_pharmay
            ORDER  BY animation_count DESC
            LIMIT  20
        """)

        anim_trend = self._q("""
            SELECT DATE_FORMAT(date_annimation, '%Y-%m')            AS month,
                   COUNT(*)                                         AS animations,
                   SUM(CASE WHEN etat = 1 THEN 1 ELSE 0 END)       AS completed,
                   COUNT(DISTINCT id_pharmay)                       AS unique_pharmacies
            FROM   t_id_pharmay_id_annimatrice_date_annimation_etat
            WHERE  date_annimation >= DATE_SUB(:ref, INTERVAL 12 MONTH)
            GROUP  BY DATE_FORMAT(date_annimation, '%Y-%m')
            ORDER  BY month
        """, {"ref": self.ref})

        # Completion rate
        total      = int(animation_summary["count"].sum()) if len(animation_summary) else 0
        completed  = int(animation_summary.loc[animation_summary["etat"] == 1, "count"].sum()) if len(animation_summary) else 0
        completion = round(completed / total * 100, 1) if total else 0

        return {
            "animation_status":         animation_summary.to_dict("records"),
            "top_animated_pharmacies":  anim_per_pharmacy.to_dict("records"),
            "monthly_trend":            anim_trend.to_dict("records"),
            "total_animations":         total,
            "completed_animations":     completed,
            "completion_rate_pct":      completion,
        }

    # =========================================================================
    # SECTION 7 — RFM
    # =========================================================================

    def rfm_analysis(self) -> dict:
        print("  [7/8] RFM analysis…")

        rfm = self._q("""
            SELECT cl,
                   DATEDIFF(:ref, MAX(DATE(date))) AS recency,
                   COUNT(DISTINCT DATE(date))       AS frequency,
                   SUM(ttc)                         AS monetary
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(date) >= DATE_SUB(:ref, INTERVAL 24 MONTH)
            GROUP  BY cl
        """, {"ref": self.ref})

        champions = pd.DataFrame()
        lost      = pd.DataFrame()
        segment_counts: dict = {}

        if len(rfm):
            rfm["r_score"] = pd.qcut(rfm["recency"], 5, labels=[5, 4, 3, 2, 1], duplicates="drop").astype(int)
            rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5], duplicates="drop").astype(int)
            rfm["m_score"] = pd.qcut(rfm["monetary"].rank(method="first"),  5, labels=[1, 2, 3, 4, 5], duplicates="drop").astype(int)
            rfm["rfm_score"] = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]

            def _segment(s):
                if s >= 13: return "CHAMPIONS"
                if s >= 10: return "LOYAL"
                if s >= 7:  return "POTENTIAL"
                if s >= 4:  return "AT_RISK"
                return "LOST"

            rfm["segment"]   = rfm["rfm_score"].apply(_segment)
            segment_counts   = rfm["segment"].value_counts().to_dict()
            champions        = rfm[rfm["segment"] == "CHAMPIONS"]
            lost             = rfm[rfm["segment"] == "LOST"]

        return {
            "segments":       segment_counts,
            "champions":      champions["cl"].tolist()   if len(champions) else [],
            "champions_count":len(champions),
            "lost_count":     len(lost),
            "lost_pharmacies":lost["cl"].tolist() if len(lost) else [],
        }

    # =========================================================================
    # SECTION 8 — OBJECTIVES
    # =========================================================================

    def objectives_analysis(self) -> dict:
        print("  [8/8] Objectives analysis…")

        # t_prime_rea_obj_r columns: prime, rea, obj, r, de, a, at
        achievement = self._q("""
            SELECT prime, rea, obj, r, de, a, at
            FROM   t_prime_rea_obj_r
            ORDER  BY rea DESC
            LIMIT  500
        """)

        # Delegate CA objectives: id_del, caph, cagro, obj, year
        del_ca = self._q("""
            SELECT d.id_del, d.caph, d.cagro, d.obj, d.year, d.prime,
                   s.revenue_12m
            FROM   t_id_del_caph_cagro_obj d
            LEFT JOIN (
                SELECT dlg, SUM(ttc) AS revenue_12m
                FROM   t_ttc_ht_qte_qte_g
                WHERE  DATE(date) >= DATE_SUB(:ref, INTERVAL 12 MONTH)
                GROUP  BY dlg
            ) s ON d.id_del = s.dlg
            ORDER  BY d.year DESC, d.obj DESC
        """, {"ref": self.ref})

        above_target = pd.DataFrame()
        below_target = pd.DataFrame()

        if len(achievement) and "rea" in achievement.columns and "obj" in achievement.columns:
            achievement["achievement_rate"] = (
                achievement["rea"] / achievement["obj"].clip(lower=1) * 100
            )
            above_target = achievement[achievement["achievement_rate"] >= 100]
            below_target = achievement[achievement["achievement_rate"] < 80]

        return {
            "total_records":      len(achievement),
            "above_target_count": len(above_target),
            "below_target_count": len(below_target),
            "raw_data":           achievement.head(20).to_dict("records"),
            "delegate_ca":        del_ca.to_dict("records"),
        }


# =============================================================================
# REPORT PRINTER
# =============================================================================

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


class DeepReportPrinter:
    def __init__(self, data: dict):
        self.data = data

    def print_all(self):
        self._header()
        self._geographic()
        self._delegates()
        self._products()
        self._pharmacies()
        self._temporal()
        self._animations()
        self._rfm()
        self._objectives()
        self._footer()

    # ── header / footer ───────────────────────────────────────────────────────

    def _header(self):
        print()
        print("=" * 62)
        print("  MEDINOTE -- DEEP CRM INTELLIGENCE REPORT")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}   (ref date: {REFERENCE_DATE})")
        print("=" * 62)

    def _footer(self):
        print()
        print("=" * 62)
        print("  End of Report -- Medinote AI Deep Analysis")
        print("=" * 62)
        print()

    # ── sections ──────────────────────────────────────────────────────────────

    def _geographic(self):
        d = self.data.get("geographic", {})
        _h("GEOGRAPHIC INTELLIGENCE")

        zones = d.get("revenue_by_zone", [])
        if zones:
            print(f"\n  Revenue by Zone (12 months):")
            print(f"  {'Zone':<20} {'Revenue':>14} {'Pharmacies':>12} {'Delegates':>10}")
            print(f"  {'-'*20} {'-'*14} {'-'*12} {'-'*10}")
            for z in zones[:12]:
                print(f"  {str(z.get('zone','?')):<20}"
                      f"  {z.get('total_revenue',0):>14,.0f}"
                      f"  {z.get('pharmacy_count',0):>12}"
                      f"  {z.get('delegate_count',0):>10}")

        gouv = d.get("revenue_by_gouv", [])
        if gouv:
            print(f"\n  Revenue by Governorate (top 10):")
            for g in gouv[:10]:
                print(f"    {str(g.get('nom_gouv','?')):<28}  {g.get('total_revenue',0):>14,.0f}")

        dead = d.get("dead_zones", [])
        if dead:
            print(f"\n  WARNING  Dead zones (no sales in 90d): {dead}")

        gaps = d.get("coverage_gaps", [])
        if gaps:
            print(f"  WARNING  Coverage gaps (no delegates): {len(gaps)} zones")

        t = d.get("top_zone", {})
        b = d.get("bottom_zone", {})
        if t and b:
            print(f"\n  Top zone:    {t.get('zone','?')} — {t.get('total_revenue',0):,.0f} TND")
            print(f"  Bottom zone: {b.get('zone','?')} — {b.get('total_revenue',0):,.0f} TND")

    def _delegates(self):
        d = self.data.get("delegates", {})
        _h("DELEGATE PERFORMANCE")

        perfs = d.get("delegate_performance", [])
        if perfs:
            print(f"\n  {'Delegate':<12} {'12M Rev':>14} {'3M Rev':>12} {'Pharmacies':>12} {'Active Days':>12} {'Efficiency':>12}")
            print(f"  {'-'*12} {'-'*14} {'-'*12} {'-'*12} {'-'*12} {'-'*12}")
            for p in perfs[:15]:
                print(f"  {str(p.get('dlg','?')):<12}"
                      f"  {p.get('revenue_12m',0):>14,.0f}"
                      f"  {p.get('revenue_3m',0):>12,.0f}"
                      f"  {p.get('pharmacies_covered',0):>12}"
                      f"  {p.get('active_days',0):>12}"
                      f"  {p.get('efficiency',0):>12,.0f}")

        avg   = d.get("avg_revenue_12m", 0)
        below = d.get("below_average_delegates", [])
        print(f"\n  Team average revenue (12m): {avg:,.0f} TND")
        print(f"  Below-average count: {len(below)}")
        if below:
            print(f"  Delegates needing support: {below[:10]}")

        vp = d.get("visit_planning", [])
        if vp:
            print(f"\n  Visit Planning (top 10 delegates):")
            for v in vp[:10]:
                print(f"    {str(v.get('delegate_id','?')):<12}  planned={v.get('planned_visits',0):>5}  days={v.get('visit_days',0):>4}  sectors={v.get('sectors_covered',0):>3}")

    def _products(self):
        d = self.data.get("products", {})
        _h("PRODUCT INTELLIGENCE")

        tops = d.get("top_products", [])
        if tops:
            print(f"\n  Top 15 Products (12 months):")
            print(f"  {'Product':<12} {'Family':<10} {'Revenue':>14} {'Qty':>10} {'Buyers':>8}")
            print(f"  {'-'*12} {'-'*10} {'-'*14} {'-'*10} {'-'*8}")
            for p in tops[:15]:
                print(f"  {str(p.get('art','?')):<12}"
                      f"  {str(p.get('fam','?')):<10}"
                      f"  {p.get('revenue_12m',0):>14,.0f}"
                      f"  {p.get('qty_12m',0):>10,.0f}"
                      f"  {p.get('buyer_count',0):>8}")

        fams = d.get("family_performance", [])
        if fams:
            print(f"\n  Product Family Performance:")
            for f in fams[:10]:
                print(f"    {str(f.get('fam','?')):<20}  {f.get('revenue_12m',0):>14,.0f}  ({f.get('product_count',0)} products, {f.get('buyer_count',0)} buyers)")

        g = d.get("growing_count", 0)
        dc = d.get("declining_count", 0)
        print(f"\n  Growing products (>+10% in 3m): {g}")
        print(f"  Declining products (>-10% in 3m): {dc}")
        dec = d.get("declining_products", [])
        if dec:
            print(f"  Declining: {dec[:15]}")

    def _pharmacies(self):
        d = self.data.get("pharmacies", {})
        _h("PHARMACY SEGMENTS")

        total = d.get("total_pharmacies", 0)
        segs  = d.get("segments", {})
        print(f"\n  Total pharmacies in DB: {total:,}")
        print()
        for seg, count in sorted(segs.items(), key=lambda x: -x[1]):
            pct = count / total * 100 if total else 0
            bar = "#" * int(pct / 3)
            print(f"  {seg:<12}  {count:>5}  ({pct:5.1f}%)  {bar}")

        fg = d.get("fast_growing_count", 0)
        print(f"\n  Fast-growing pharmacies (+50% in 3m): {fg}")

        tops = d.get("top_pharmacies", [])
        if tops:
            print(f"\n  Top 10 Pharmacies by Lifetime Revenue:")
            for p in tops[:10]:
                print(f"    {str(p.get('cl','?')):<15}  zone={str(p.get('zone','?')):<12}  "
                      f"{p.get('revenue_total',0):>14,.0f}  [{p.get('segment','?')}]  "
                      f"inactive={p.get('days_inactive',0)}d")

    def _temporal(self):
        d = self.data.get("temporal", {})
        _h("TEMPORAL ANALYSIS")

        yearly = d.get("yearly_comparison", [])
        if yearly:
            print(f"\n  Year over Year Revenue:")
            prev = None
            for y in yearly:
                rev  = y.get("revenue", 0)
                yoy  = f"  ({(rev-prev)/prev*100:+.1f}% YoY)" if prev else ""
                print(f"    {y.get('year','?')}:  {rev:>14,.0f} TND   ({y.get('pharmacies',0)} pharmacies){yoy}")
                prev = rev if rev else prev

        best  = d.get("best_month")
        worst = d.get("worst_month")
        if best:
            print(f"\n  Best month historically:  {MONTHS[best-1]}")
        if worst:
            print(f"  Worst month historically: {MONTHS[worst-1]}")

        yoy = d.get("yoy_growth_pct")
        if yoy is not None:
            arrow = "+" if yoy >= 0 else ""
            print(f"  YoY growth (last full year): {arrow}{yoy:.1f}%")

        monthly = d.get("monthly_trend", [])
        if monthly:
            print(f"\n  Last 6 months trend:")
            for m in monthly[-6:]:
                rev = m.get("revenue", 0)
                bar = "#" * min(40, int(rev / 50_000))
                print(f"    {m.get('month','?')}  {rev:>14,.0f}  {bar}")

    def _animations(self):
        d = self.data.get("animations", {})
        _h("ANIMATION ANALYSIS")

        total      = d.get("total_animations", 0)
        completed  = d.get("completed_animations", 0)
        rate       = d.get("completion_rate_pct", 0)
        print(f"\n  Total animations: {total:,}")
        print(f"  Completed:        {completed:,}  ({rate:.1f}%)")

        status = d.get("animation_status", [])
        if status:
            print(f"\n  By status:")
            for s in status:
                print(f"    etat={s.get('etat','?')}:  {s.get('count',0):,}")

        trend = d.get("monthly_trend", [])
        if trend:
            print(f"\n  Last 6 months animation activity:")
            for m in trend[-6:]:
                print(f"    {m.get('month','?')}  planned={m.get('animations',0):>5}  "
                      f"completed={m.get('completed',0):>5}  "
                      f"pharmacies={m.get('unique_pharmacies',0):>5}")

    def _rfm(self):
        d = self.data.get("rfm", {})
        _h("RFM CUSTOMER SEGMENTS")

        segs  = d.get("segments", {})
        total = sum(segs.values()) if segs else 0
        seg_order = ["CHAMPIONS", "LOYAL", "POTENTIAL", "AT_RISK", "LOST"]
        labels    = {"CHAMPIONS": "Champions", "LOYAL": "Loyal",
                     "POTENTIAL": "Potential", "AT_RISK": "At Risk", "LOST": "Lost"}
        print()
        for seg in seg_order:
            count = segs.get(seg, 0)
            pct   = count / total * 100 if total else 0
            bar   = "#" * int(pct / 4)
            print(f"  {labels[seg]:<12}  {count:>5}  ({pct:5.1f}%)  {bar}")

        print(f"\n  Champions (highest-value):  {d.get('champions_count', 0)}")
        print(f"  Lost (win-back targets):    {d.get('lost_count', 0)}")
        lost = d.get("lost_pharmacies", [])
        if lost:
            print(f"  Sample lost pharmacies: {lost[:10]}")

    def _objectives(self):
        d = self.data.get("objectives", {})
        _h("OBJECTIVES VS ACHIEVEMENT")

        above = d.get("above_target_count", 0)
        below = d.get("below_target_count", 0)
        total = d.get("total_records", 0)
        print(f"\n  Records analysed:      {total:,}")
        print(f"  Above target (>=100%): {above:,}")
        print(f"  Below target (<80%):   {below:,}")

        ca = d.get("delegate_ca", [])
        if ca:
            print(f"\n  Delegate CA vs Objectives (latest year):")
            print(f"  {'Delegate':<12} {'Year':>6} {'Objective':>12} {'CA Pharma':>12} {'Actual Rev':>12}")
            print(f"  {'-'*12} {'-'*6} {'-'*12} {'-'*12} {'-'*12}")
            for row in ca[:15]:
                print(f"  {str(row.get('id_del','?')):<12}"
                      f"  {str(row.get('year','?')):>6}"
                      f"  {row.get('obj',0) or 0:>12,.0f}"
                      f"  {row.get('caph',0) or 0:>12,.0f}"
                      f"  {row.get('revenue_12m',0) or 0:>12,.0f}")


# ─── utility ──────────────────────────────────────────────────────────────────

def _h(title: str):
    print(f"\n\n{'-'*62}")
    print(f"  {title}")
    print(f"{'-'*62}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)

    db      = MedinoteDB()
    engine  = DeepAnalysis(db)
    data    = engine.run_all()

    printer = DeepReportPrinter(data)
    printer.print_all()

    os.makedirs(REPORTS_DIR, exist_ok=True)
    out = os.path.join(REPORTS_DIR, "deep_analysis.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    print(f"Raw data saved -> {out}")
    db.close()
