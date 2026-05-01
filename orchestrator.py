"""
Medinote -- Multi-Agent Orchestration System
5 agents: Orchestrator, Intent, Data, Prediction, Explanation.
"""

import sys
import os
import json
import logging
import warnings
from datetime import datetime

import numpy as np
import pandas as pd
import joblib
from sqlalchemy import text

warnings.filterwarnings("ignore")
sys.path.append(r"c:\Users\omri\Desktop\pii")
from db_layer import MedinoteDB, FeatureBuilder
from capability_checker import CapabilityChecker

try:
    from openai import OpenAI as _OpenAI
except ImportError:
    _OpenAI = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("medinote")

MODELS_DIR    = r"c:\Users\omri\Desktop\pii\models"
REGISTRY_PATH = os.path.join(MODELS_DIR, "model_registry.json")


OPENROUTER_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL_FAST  = "google/gemma-3-4b-it:free"   # intent extraction
OPENROUTER_MODEL_SMART = "google/gemma-3-12b-it:free"  # explanation


def _resolve_api_key(provided: str = "") -> str:
    """
    Returns OpenRouter key from (in priority order):
    1. provided argument
    2. OPENROUTER_API_KEY env var
    3. ~/.claude/config.json  openrouterApiKey field
    """
    key = provided or os.getenv("OPENROUTER_API_KEY", "")
    if key:
        return key
    config_path = os.path.join(os.path.expanduser("~"), ".claude", "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                cfg = json.load(f)
            key = cfg.get("openrouterApiKey", "")
            if key:
                log.info("OpenRouter key loaded from ~/.claude/config.json")
        except Exception as exc:
            log.warning("Could not read Claude config: %s", exc)
    return key


def _make_llm_client(api_key: str):
    if not _OpenAI or not api_key:
        return None
    return _OpenAI(api_key=api_key, base_url=OPENROUTER_BASE)


# =============================================================================
# AGENT 1 — IntentAgent  (LLM via OpenRouter + rule-based fallback)
# =============================================================================

class IntentAgent:
    """
    Keyword-based intent extractor.
    Covers all 15 task_ids with multi-language support (FR/EN/AR).
    Falls back to LLM if api_key is provided and keyword match is ambiguous.
    """

    # (task_id, entity_type, keywords_en, keywords_fr)
    _RULES = [
        ("pharmacy_churn_risk", "pharmacy",
         ["churn", "leaving", "lost", "inactive", "risk of losing", "at risk", "abandon"],
         ["churn", "partir", "perdre", "inactif", "risque", "abandonne", "quitter", "fidelite"]),

        ("sales_forecast_30d", "pharmacy",
         ["sales forecast", "revenue forecast", "predict revenue", "forecast sales",
          "next month revenue", "expected sales", "forecast 30", "revenue next month",
          "total sales next", "total revenue next", "sales next 30", "sales in 30",
          "next 30 days sales", "predict sales", "future sales",
          "total sales be", "sales be next", "total sales", "sales 30 days",
          "revenue 30 days", "next 30 days"],
         ["prevision vente", "prevision chiffre", "prevoir chiffre", "revenu futur",
          "ventes prevues", "chiffre affaire prochain mois", "ventes prochains",
          "chiffre prochain", "prevision 30 jours"]),

        ("product_demand_forecast", "product",
         ["product demand", "demand forecast", "high demand", "which products",
          "product next month", "stock forecast", "demand next"],
         ["demande produit", "prevision demande", "forte demande", "quels produits",
          "stock prevu", "produit mois prochain"]),

        ("delegate_performance_score", "delegate",
         ["delegate performance", "best delegate", "top delegate", "delegate score",
          "delegate ranking", "sales rep performance", "agent performance",
          "best performing delegate", "performing delegate", "delegate result",
          "delegate", "sales rep", "agent"],
         ["performance delegue", "meilleur delegue", "top delegue", "score delegue",
          "classement delegue", "agent commercial", "delegue performance",
          "delegue", "commercial"]),

        ("payment_default_risk", "pharmacy",
         ["payment default", "default on payment", "default payment", "payment risk",
          "will not pay", "default risk", "credit risk", "payment problem", "unpaid",
          "likely to default", "payment failure"],
         ["risque paiement", "defaut paiement", "impaye", "risque credit",
          "probleme paiement", "ne paiera pas"]),

        ("order_cancellation_risk", "pharmacy",
         ["cancel", "cancellation", "order cancel", "will cancel", "cancel risk",
          "might cancel", "cancel order", "cancel their order", "at risk of cancelling",
          "stop ordering", "cancelling order"],
         ["annulation", "annuler", "risque annulation", "commande annulee",
          "risque de cancellation", "pourrait annuler"]),

        ("pharmacy_tier_upgrade", "pharmacy",
         ["tier upgrade", "tier promotion", "upgrade pharmacy", "promote client",
          "tier level", "vip upgrade", "segment upgrade"],
         ["montee tier", "promotion client", "upgrade", "niveau client",
          "changer segment", "passer vip"]),

        ("product_sales_trend", "product",
         ["product trend", "sales trend", "trending product", "product growth",
          "product decline", "product evolution", "downtrend"],
         ["tendance produit", "trend vente", "produit tendance", "evolution produit",
          "croissance produit", "baisse produit"]),

        ("campaign_response_probability", "pharmacy",
         ["campaign", "marketing campaign", "will respond", "campaign response",
          "email campaign", "promotion response", "who will buy"],
         ["campagne", "repondre campagne", "probabilite campagne",
          "qui va repondre", "promotions", "qui acheter"]),

        ("cross_sell_ranking", "product",
         ["cross sell", "cross-sell", "recommend product", "upsell",
          "suggest product", "what else", "complementary product"],
         ["vente croisee", "cross sell", "recommander produit", "suggerer",
          "produit complementaire", "que vendre aussi"]),

        ("visit_priority_ranking", "pharmacy",
         ["visit priority", "who to visit", "visit first", "visit list",
          "priority visit", "schedule visit", "which pharmacy visit"],
         ["priorite visite", "qui visiter", "visiter en premier", "liste visite",
          "planifier visite", "quelle pharmacie visiter", "visite cette semaine"]),

        ("delegate_target_achievement", "delegate",
         ["target achievement", "meet target", "hit quota", "miss target",
          "quota attainment", "delegate target", "will reach target",
          "hit their target", "hit target", "reach their target", "reach target",
          "will achieve", "achieve target", "meet their quota", "delegates hit"],
         ["atteindre objectif", "objectif delegue", "quota", "manquer objectif",
          "atteinte cible", "delegue objectif", "atteindre cible",
          "qui va atteindre", "objectif delegues"]),

        ("complaint_recurrence_risk", "pharmacy",
         ["complaint", "recurrence complaint", "complain again", "complaint risk",
          "repeat complaint", "dissatisfied", "problem recurrence"],
         ["reclamation", "plainte", "risque reclamation", "plainte repetee",
          "client insatisfait", "probleme recurrent"]),

        ("delegate_activity_drop", "delegate",
         ["delegate activity drop", "delegate inactive", "delegate slow down",
          "delegate less active", "delegate drop", "agent decline",
          "reduced their activity", "reduce activity", "activity reduced",
          "decreased activity", "less active delegates", "activity decline",
          "delegates reduced", "dropping activity", "lower activity"],
         ["baisse activite delegue", "delegue inactif", "delegue moins actif",
          "chute activite", "delegue ralentit", "activite reduite",
          "delegue reduit", "moins d activite"]),

        ("pharmacy_next_purchase_date", "pharmacy",
         ["next purchase", "next order", "when will order", "next buy",
          "reorder date", "expected order date", "next visit"],
         ["prochain achat", "prochaine commande", "quand commandera",
          "date prochain ordre", "prochaine visite commande"]),
    ]

    # Urgency signals
    _URGENT_KW  = ["urgent", "critical", "now", "immediately", "asap",
                   "today", "this week", "prioritaire", "maintenant", "aujourd"]
    _LOW_KW     = ["maybe", "sometime", "general", "overview", "report",
                   "peut-etre", "general", "apercu"]

    SYSTEM = """You are an intent extraction agent for Medinote, a pharmaceutical CRM.

Extract the intent from the user request and return ONLY valid JSON — no explanation, no markdown.

Available task_ids:
pharmacy_churn_risk, sales_forecast_30d, product_demand_forecast,
delegate_performance_score, payment_default_risk, order_cancellation_risk,
pharmacy_tier_upgrade, product_sales_trend, campaign_response_probability,
cross_sell_ranking, visit_priority_ranking, delegate_target_achievement,
complaint_recurrence_risk, delegate_activity_drop, pharmacy_next_purchase_date

Return this exact JSON structure:
{"task_id":"<matched task or unknown>","entity_type":"pharmacy/delegate/product/order","entity_id":"<specific ID or null>","time_horizon":"<30d default>","urgency":"high/medium/low","confidence":<0.0-1.0>,"original_request":"<verbatim>"}"""

    def __init__(self, api_key: str = ""):
        self._client = _make_llm_client(api_key)

    def extract_intent(self, user_request: str) -> dict:
        # Try LLM first
        if self._client:
            try:
                resp = self._client.chat.completions.create(
                    model=OPENROUTER_MODEL_FAST,
                    max_tokens=256,
                    temperature=0,
                    messages=[
                        {"role": "user", "content": self.SYSTEM + "\n\nUser request: " + user_request},
                    ],
                )
                raw = resp.choices[0].message.content.strip()
                # Strip markdown fences if model wraps in ```json
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                intent = json.loads(raw.strip())
                intent.setdefault("original_request", user_request)
                # Normalize entity_id: LLM sometimes returns string "null"/"none"
                eid = intent.get("entity_id")
                if isinstance(eid, str) and eid.lower() in ("null", "none", ""):
                    intent["entity_id"] = None
                log.info("Intent (LLM): task=%s confidence=%.2f",
                         intent.get("task_id"), intent.get("confidence", 0))
                return intent
            except json.JSONDecodeError:
                log.warning("Intent LLM returned invalid JSON — falling back to rules")
            except Exception as exc:
                log.warning("Intent LLM error (%s) — falling back to rules", exc)

        # Rule-based fallback
        return self._rule_extract(user_request)

    def _rule_extract(self, user_request: str) -> dict:
        import re
        lower = user_request.lower()
        best_task, best_entity, best_score = "unknown", "pharmacy", 0

        for task_id, entity_type, kw_en, kw_fr in self._RULES:
            score = sum(
                (2 if len(kw) > 8 else 1)
                for kw in kw_en + kw_fr if kw in lower
            )
            if score > best_score:
                best_score  = score
                best_task   = task_id
                best_entity = entity_type

        confidence = min(0.97, best_score * 0.25) if best_score > 0 else 0.0
        urgency = "medium"
        if any(kw in lower for kw in self._URGENT_KW):
            urgency = "high"
        elif any(kw in lower for kw in self._LOW_KW):
            urgency = "low"

        matches   = re.findall(r'\b([A-Z0-9]{3,}[A-Z0-9\-]*[0-9]+)\b', user_request)
        entity_id = matches[0] if matches else None

        log.info("Intent (rules): task=%s confidence=%.2f", best_task, confidence)
        return {
            "task_id":          best_task,
            "entity_type":      best_entity,
            "entity_id":        entity_id,
            "time_horizon":     "30d",
            "urgency":          urgency,
            "confidence":       round(confidence, 2),
            "original_request": user_request,
        }

    def is_unknown(self, intent: dict) -> bool:
        return (
            intent.get("task_id") == "unknown"
            or intent.get("confidence", 0) < 0.5
        )

    @staticmethod
    def _unknown(user_request: str) -> dict:
        return {
            "task_id":          "unknown",
            "entity_type":      None,
            "entity_id":        None,
            "time_horizon":     "30d",
            "urgency":          "low",
            "confidence":       0.0,
            "original_request": user_request,
        }


# =============================================================================
# AGENT 2 — DataAgent
# =============================================================================

class DataAgent:
    def __init__(self, db: MedinoteDB):
        self.db = db
        self.fb = FeatureBuilder(db)
        self._churn_cache = None
        self._dlg_cache   = None
        self._prod_cache  = None

    # ── cache helpers ─────────────────────────────────────────────────────────

    def _churn(self) -> pd.DataFrame:
        if self._churn_cache is None:
            log.info("Loading pharmacy_churn_features() …")
            self._churn_cache = self.fb.pharmacy_churn_features()
        return self._churn_cache

    def _dlg_perf(self) -> pd.DataFrame:
        if self._dlg_cache is None:
            log.info("Loading delegate_performance_features() …")
            self._dlg_cache = self.fb.delegate_performance_features()
        return self._dlg_cache

    def _prod(self) -> pd.DataFrame:
        if self._prod_cache is None:
            log.info("Loading product_demand_features() …")
            self._prod_cache = self.fb.product_demand_features()
        return self._prod_cache

    # ── public entry point ────────────────────────────────────────────────────

    def get_features(self, intent: dict) -> pd.DataFrame:
        routing = {
            "pharmacy_churn_risk":           self._pharmacy_churn_features,
            "sales_forecast_30d":            self._sales_forecast_features,
            "product_demand_forecast":       self._product_demand_features,
            "delegate_performance_score":    self._delegate_perf_features,
            "payment_default_risk":          self._payment_features,
            "order_cancellation_risk":       self._cancellation_features,
            "pharmacy_tier_upgrade":         self._tier_features,
            "product_sales_trend":           self._trend_features,
            "campaign_response_probability": self._campaign_features,
            "cross_sell_ranking":            self._crosssell_features,
            "visit_priority_ranking":        self._visit_features,
            "delegate_target_achievement":   self._delegate_target_features,
            "complaint_recurrence_risk":     self._complaint_features,
            "delegate_activity_drop":        self._delegate_activity_features,
            "pharmacy_next_purchase_date":   self._next_purchase_features,
        }

        builder = routing.get(intent["task_id"])
        if builder is None:
            raise ValueError(f"No data builder for task_id={intent['task_id']}")

        df = builder()

        entity_id = intent.get("entity_id")
        if entity_id:
            entity_col = self._entity_col(intent.get("entity_type", "pharmacy"))
            if entity_col in df.columns:
                df = df[df[entity_col] == str(entity_id)].reset_index(drop=True)

        log.info("DataAgent: %d rows, %d cols for %s",
                 len(df), len(df.columns), intent["task_id"])
        return df

    @staticmethod
    def _entity_col(entity_type: str) -> str:
        return {"pharmacy": "cl", "delegate": "dlg",
                "product": "art", "order": "cl"}.get(entity_type, "cl")

    # ── routed feature builders ───────────────────────────────────────────────

    def _pharmacy_churn_features(self) -> pd.DataFrame:
        return self._churn().copy()

    def _sales_forecast_features(self) -> pd.DataFrame:
        df = self.fb.sales_forecast_features()
        df["revenue_growth_rate"] = df["revenue_60d"] / (df["revenue_90d"] + 1)
        df["order_regularity"]    = df["order_count_90d"] / 3.0
        return df

    def _product_demand_features(self) -> pd.DataFrame:
        df = self._prod().copy()
        df["has_recent_sales"]  = (df["revenue_60d"] > 0).astype(int)
        df["sales_consistency"] = (
            (df["revenue_60d"] > 0).astype(int) +
            (df["revenue_90d"] > 0).astype(int)
        )
        return df

    def _delegate_perf_features(self) -> pd.DataFrame:
        return self._dlg_perf().copy()

    def _payment_features(self) -> pd.DataFrame:
        sum180 = self.db.get_pharmacy_summary(days=180).rename(columns={
            "revenue_total": "revenue_last_180d",
            "order_count":   "order_count_last_180d",
        })

        prev180 = self.db.query(text("""
            SELECT cl,
                   COUNT(DISTINCT DATE(`date`)) AS order_count_prev_180d
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(`date`) >= :from_date
              AND  DATE(`date`) <  :to_date
            GROUP  BY cl
        """), {"from_date": self.db._cutoff(360), "to_date": self.db._cutoff(180)})

        df = sum180[["cl", "revenue_last_180d",
                     "order_count_last_180d", "days_since_last_order"]].copy()
        df = df.merge(prev180, on="cl", how="left")
        df["order_frequency"] = df["order_count_last_180d"] / 180.0
        return df.fillna(0)

    def _cancellation_features(self) -> pd.DataFrame:
        churn = self._churn()

        w30 = self.db.query(text("""
            SELECT cl, COUNT(DISTINCT DATE(`date`)) AS order_count_last_30d
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(`date`) >= :cutoff
            GROUP  BY cl
        """), {"cutoff": self.db._cutoff(30)})

        prev30 = self.db.query(text("""
            SELECT cl, COUNT(DISTINCT DATE(`date`)) AS order_count_prev_30d
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(`date`) >= :from_date
              AND  DATE(`date`) <  :to_date
            GROUP  BY cl
        """), {"from_date": self.db._cutoff(60), "to_date": self.db._cutoff(30)})

        df = churn[["cl", "revenue_90d", "days_since_last_order", "revenue_trend"]].copy()
        df = df.merge(w30,   on="cl", how="left")
        df = df.merge(prev30, on="cl", how="left")
        return df.fillna(0)

    def _tier_features(self) -> pd.DataFrame:
        churn = self._churn()

        sum90 = self.db.get_pharmacy_summary(days=90).rename(columns={
            "revenue_total": "revenue_last_90d",
            "order_count":   "order_count_last_90d",
        })

        prev90 = self.db.query(text("""
            SELECT cl,
                   SUM(ttc)                              AS revenue_prev_90d,
                   COUNT(DISTINCT DATE(`date`))          AS order_count_prev_90d
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(`date`) >= :from_date
              AND  DATE(`date`) <  :to_date
            GROUP  BY cl
        """), {"from_date": self.db._cutoff(180), "to_date": self.db._cutoff(90)})

        df = sum90[["cl", "revenue_last_90d", "order_count_last_90d"]].copy()
        df = df.merge(prev90, on="cl", how="left")
        df = df.merge(
            churn[["cl", "days_since_last_order", "revenue_trend", "churn_label"]],
            on="cl", how="left",
        )
        return df.fillna(0)

    def _trend_features(self) -> pd.DataFrame:
        prod = self._prod()

        prev30 = self.db.query(text("""
            SELECT art, SUM(ttc) AS revenue_prev_30d
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(`date`) >= :from_date
              AND  DATE(`date`) <  :to_date
            GROUP  BY art
        """), {"from_date": self.db._cutoff(60), "to_date": self.db._cutoff(30)})

        prev60 = self.db.query(text("""
            SELECT art, SUM(ttc) AS revenue_prev_60d
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(`date`) >= :from_date
              AND  DATE(`date`) <  :to_date
            GROUP  BY art
        """), {"from_date": self.db._cutoff(90), "to_date": self.db._cutoff(60)})

        df = prod[["art", "revenue_30d", "revenue_90d", "distinct_buyers_90d"]].copy()
        df = df.rename(columns={"revenue_30d": "revenue_last_30d"})
        df = df.merge(prev30, on="art", how="left")
        df = df.merge(prev60, on="art", how="left")
        return df.fillna(0)

    def _campaign_features(self) -> pd.DataFrame:
        churn = self._churn()
        return churn[["cl", "days_since_last_order", "order_count_30d",
                      "order_count_90d", "revenue_30d", "revenue_90d",
                      "revenue_trend", "churn_label"]].copy()

    def _crosssell_features(self) -> pd.DataFrame:
        churn = self._churn()
        prod  = self._prod()

        total_pharm = max(len(churn), 1)
        pop = self.db.query(text("""
            SELECT art, COUNT(DISTINCT cl) AS buyer_count
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(`date`) >= :cutoff
            GROUP  BY art
        """), {"cutoff": self.db._cutoff(90)})
        pop["product_popularity_pct"] = pop["buyer_count"] / total_pharm

        pharm_f = churn[["cl", "days_since_last_order", "revenue_90d",
                         "order_count_90d", "churn_label"]].copy()
        pharm_f = pharm_f.rename(columns={
            "revenue_90d":    "pharmacy_revenue_90d",
            "order_count_90d": "pharmacy_order_count_90d",
        })

        prod_f = prod[["art", "revenue_90d", "distinct_buyers_90d"]].copy()
        prod_f = prod_f.rename(columns={"revenue_90d": "product_revenue_90d"})
        prod_f = prod_f.merge(pop[["art", "product_popularity_pct"]],
                              on="art", how="left")

        pharm_f["_k"] = 1
        prod_f["_k"]  = 1
        pairs = pharm_f.merge(prod_f, on="_k").drop(columns=["_k"])

        bought = self.db.query(text("""
            SELECT DISTINCT cl, art
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(`date`) >= :cutoff
        """), {"cutoff": self.db._cutoff(90)})
        bought["_b"] = 1
        pairs = pairs.merge(bought, on=["cl", "art"], how="left")
        pairs = pairs[pairs["_b"].isna()].drop(columns=["_b"])

        if len(pairs) > 50000:
            pairs = pairs.sample(50000, random_state=42).reset_index(drop=True)

        return pairs.fillna(0)

    def _visit_features(self) -> pd.DataFrame:
        churn = self._churn()
        df = churn[["cl", "days_since_last_order", "revenue_90d",
                    "order_count_90d", "revenue_trend", "churn_label"]].copy()
        return df.rename(columns={
            "days_since_last_order": "days_since_last_sale",
            "revenue_90d":           "revenue_last_90d",
        })

    def _delegate_target_features(self) -> pd.DataFrame:
        dlg = self._dlg_perf()

        w30 = self.db.query(text("""
            SELECT dlg, SUM(ttc) AS revenue_last_30d
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(`date`) >= :cutoff
              AND  dlg IS NOT NULL AND dlg != ''
            GROUP  BY dlg
        """), {"cutoff": self.db._cutoff(30)})

        prev30 = self.db.query(text("""
            SELECT dlg, SUM(ttc) AS revenue_prev_30d
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(`date`) >= :from_date
              AND  DATE(`date`) <  :to_date
              AND  dlg IS NOT NULL AND dlg != ''
            GROUP  BY dlg
        """), {"from_date": self.db._cutoff(60), "to_date": self.db._cutoff(30)})

        prev60 = self.db.query(text("""
            SELECT dlg, SUM(ttc) AS revenue_prev_60d
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(`date`) >= :from_date
              AND  DATE(`date`) <  :to_date
              AND  dlg IS NOT NULL AND dlg != ''
            GROUP  BY dlg
        """), {"from_date": self.db._cutoff(90), "to_date": self.db._cutoff(60)})

        df = dlg[["dlg", "order_count_90d",
                  "distinct_pharmacies_90d", "performance_score"]].copy()
        df = df.merge(w30,   on="dlg", how="left")
        df = df.merge(prev30, on="dlg", how="left")
        df = df.merge(prev60, on="dlg", how="left")
        return df.fillna(0)

    def _complaint_features(self) -> pd.DataFrame:
        churn = self._churn()

        gaps = self.db.query(text("""
            SELECT cl, MAX(gap) AS max_gap_between_orders
            FROM (
                SELECT cl,
                       DATEDIFF(`date`,
                           LAG(`date`) OVER (PARTITION BY cl ORDER BY `date`)
                       ) AS gap
                FROM (
                    SELECT cl, DATE(`date`) AS `date`
                    FROM   t_ttc_ht_qte_qte_g
                    WHERE  DATE(`date`) >= :cutoff
                    GROUP  BY cl, DATE(`date`)
                ) daily
            ) gaps
            WHERE gap IS NOT NULL
            GROUP BY cl
        """), {"cutoff": self.db._cutoff(180)})

        df = churn[["cl", "order_count_180d", "revenue_90d",
                    "order_count_90d", "churn_label"]].copy()
        df = df.rename(columns={"order_count_180d": "order_count_last_180d"})
        df = df.merge(gaps, on="cl", how="left")
        return df.fillna(0)

    def _delegate_activity_features(self) -> pd.DataFrame:
        dlg = self._dlg_perf()

        w30 = self.db.query(text("""
            SELECT dlg, COUNT(DISTINCT DATE(`date`)) AS order_count_last_30d
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(`date`) >= :cutoff
              AND  dlg IS NOT NULL AND dlg != ''
            GROUP  BY dlg
        """), {"cutoff": self.db._cutoff(30)})

        prev30 = self.db.query(text("""
            SELECT dlg, COUNT(DISTINCT DATE(`date`)) AS order_count_prev_30d
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(`date`) >= :from_date
              AND  DATE(`date`) <  :to_date
              AND  dlg IS NOT NULL AND dlg != ''
            GROUP  BY dlg
        """), {"from_date": self.db._cutoff(60), "to_date": self.db._cutoff(30)})

        df = dlg[["dlg", "revenue_90d",
                  "distinct_pharmacies_90d", "performance_score"]].copy()
        df = df.merge(w30,   on="dlg", how="left")
        df = df.merge(prev30, on="dlg", how="left")
        return df.fillna(0)

    def _next_purchase_features(self) -> pd.DataFrame:
        churn = self._churn()

        totals = self.db.query(text("""
            SELECT cl, COUNT(DISTINCT DATE(`date`)) AS order_count
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(`date`) >= :cutoff
            GROUP  BY cl
        """), {"cutoff": self.db._cutoff(365)})

        df = churn[["cl", "days_since_last_order", "revenue_90d",
                    "order_count_90d", "revenue_trend"]].copy()
        df = df.rename(columns={"days_since_last_order": "days_since_last_sale"})
        df = df.merge(totals, on="cl", how="left")
        return df.fillna(0)


# =============================================================================
# AGENT 3 — PredictionAgent
# =============================================================================

class PredictionAgent:
    _DELEGATE_TASKS = {
        "delegate_performance_score",
        "delegate_target_achievement",
        "delegate_activity_drop",
    }
    _PRODUCT_TASKS = {
        "product_demand_forecast",
        "product_sales_trend",
        "cross_sell_ranking",
    }

    def __init__(self, models_dir: str, registry_path: str):
        self.models_dir    = models_dir
        self.registry      = self._load_registry(registry_path)
        self._loaded       = {}

    @staticmethod
    def _load_registry(path: str) -> dict:
        with open(path) as f:
            return json.load(f)

    def _load_model(self, task_id: str):
        if task_id not in self._loaded:
            task       = self.registry.get(task_id, {})
            model_path = task.get("model_path", "")
            if model_path and os.path.exists(model_path):
                self._loaded[task_id] = joblib.load(model_path)
                log.info("Model loaded: %s", os.path.basename(model_path))
            else:
                log.warning("Model file not found for %s: %s", task_id, model_path)
        return self._loaded.get(task_id)

    def _select_features(self, task_id: str, df: pd.DataFrame) -> pd.DataFrame:
        task          = self.registry.get(task_id, {})
        features_path = task.get("features_path", "")
        if features_path and os.path.exists(features_path):
            with open(features_path) as f:
                expected = json.load(f)
            available = [c for c in expected if c in df.columns]
            missing   = [c for c in expected if c not in df.columns]
            if missing:
                log.warning("Missing features for %s: %s", task_id, missing)
            return df[available].fillna(0)

        exclude = {"cl", "dlg", "art", "churn_label", "_k", "_b"}
        cols = [c for c in df.columns if c not in exclude]
        return df[cols].fillna(0)

    def safe_predict(self, model, X: pd.DataFrame, task_type: str = "classification"):
        if task_type == "classification":
            proba = model.predict_proba(X)
            return proba[:, 1] if proba.shape[1] > 1 else proba[:, 0]
        return np.maximum(0, model.predict(X))

    def predict(self, task_id: str, features: pd.DataFrame) -> dict:
        task      = self.registry.get(task_id, {})
        mode      = task.get("mode_active", "mode2")
        task_type = task.get("type", "classification")

        if mode == "mode1":
            model = self._load_model(task_id)
            if model is None:
                return self._mode2_fallback(task_id, features, task)

            X           = self._select_features(task_id, features)
            predictions = self.safe_predict(model, X, task_type)
            entity_col  = self._entity_col(task_id)

            results = []
            for i, (_, row) in enumerate(features.iterrows()):
                score = float(predictions[i])
                entity_id = (
                    f"{row.get('cl', i)}::{row.get('art', i)}"
                    if task_id == "cross_sell_ranking"
                    else str(row.get(entity_col, i))
                )
                results.append({
                    "entity_id":      entity_id,
                    "score":          round(score, 4),
                    "confidence_pct": round(score * 100, 1),
                    "risk_level":     self._risk_level(score, task_type),
                })

            results.sort(key=lambda x: x["score"], reverse=True)

            return {
                "task_id":        task_id,
                "mode":           "mode1",
                "model_used":     os.path.basename(task.get("model_path", "")),
                "total_entities": len(results),
                "results":        results,
                "metric_score":   task.get("optimized_score")
                                  or task.get("honest_auc")
                                  or task.get(f"baseline_{task.get('metric_name','auc')}", 0),
            }

        return self._mode2_fallback(task_id, features, task)

    def _mode2_fallback(self, task_id: str, features: pd.DataFrame, task: dict) -> dict:
        rule = task.get("fallback_rule", task.get("notes", "No rule defined"))
        return {
            "task_id":        task_id,
            "mode":           "mode2",
            "fallback_rule":  rule,
            "total_entities": len(features),
            "results":        [],
            "caveat":         "Rule-based analysis — not a model prediction",
            "metric_score":   0,
        }

    @staticmethod
    def _risk_level(score: float, task_type: str) -> str:
        if task_type == "regression":
            return "value"
        if score >= 0.75:
            return "HIGH"
        if score >= 0.50:
            return "MEDIUM"
        return "LOW"

    def _entity_col(self, task_id: str) -> str:
        if task_id in self._DELEGATE_TASKS:
            return "dlg"
        if task_id in self._PRODUCT_TASKS:
            return "art"
        return "cl"


# =============================================================================
# AGENT 4 — ExplanationAgent  (template-based, no API required)
# =============================================================================

class ExplanationAgent:
    """
    Generates structured business explanations from prediction results.
    Multi-language: detects FR/AR/EN from the original request.
    No external API needed.
    """

    _TASK_LABELS = {
        "pharmacy_churn_risk":           ("Churn Risk",           "Risque de Churn"),
        "sales_forecast_30d":            ("30-Day Sales Forecast", "Prevision Ventes 30j"),
        "product_demand_forecast":       ("Product Demand",        "Demande Produit"),
        "delegate_performance_score":    ("Delegate Performance",  "Performance Delegue"),
        "payment_default_risk":          ("Payment Default Risk",  "Risque Impaye"),
        "order_cancellation_risk":       ("Cancellation Risk",     "Risque Annulation"),
        "pharmacy_tier_upgrade":         ("Tier Upgrade",          "Promotion Tier"),
        "product_sales_trend":           ("Product Trend",         "Tendance Produit"),
        "campaign_response_probability": ("Campaign Response",     "Reponse Campagne"),
        "cross_sell_ranking":            ("Cross-Sell Opportunity","Opportunite Cross-Sell"),
        "visit_priority_ranking":        ("Visit Priority",        "Priorite Visite"),
        "delegate_target_achievement":   ("Target Achievement",    "Atteinte Objectif"),
        "complaint_recurrence_risk":     ("Complaint Risk",        "Risque Reclamation"),
        "delegate_activity_drop":        ("Activity Drop",         "Baisse Activite"),
        "pharmacy_next_purchase_date":   ("Next Purchase Date",    "Prochain Achat"),
    }

    _ACTIONS = {
        "pharmacy_churn_risk":           ("Contact these pharmacies immediately to prevent churn.",
                                          "Contactez ces pharmacies immediatement pour eviter le churn."),
        "sales_forecast_30d":            ("Prepare stock and delegate assignments for forecasted demand.",
                                          "Preparez le stock et l'affectation des delegues selon la prevision."),
        "product_demand_forecast":       ("Prioritize restocking for high-demand products.",
                                          "Reapprovisionner en priorite les produits a forte demande."),
        "delegate_performance_score":    ("Reward top performers and support underperforming delegates.",
                                          "Recompensez les meilleurs et accompagnez les delegues en difficulte."),
        "payment_default_risk":          ("Review payment terms with high-risk pharmacies.",
                                          "Revoyez les conditions de paiement avec les pharmacies a risque."),
        "order_cancellation_risk":       ("Reach out proactively to at-risk pharmacies before orders cancel.",
                                          "Contactez proactivement les pharmacies a risque avant annulation."),
        "pharmacy_tier_upgrade":         ("Offer loyalty benefits to pharmacies ready for tier promotion.",
                                          "Proposez des avantages fidelite aux pharmacies pretes a monter de tier."),
        "product_sales_trend":           ("Deprioritize declining products and push growing ones.",
                                          "Deprioritisez les produits en baisse et poussez ceux en croissance."),
        "campaign_response_probability": ("Focus campaign budget on the highest-probability responders.",
                                          "Concentrez le budget campagne sur les pharmacies les plus susceptibles de repondre."),
        "cross_sell_ranking":            ("Instruct delegates to pitch these products on their next visits.",
                                          "Demandez aux delegues de proposer ces produits lors de leurs prochaines visites."),
        "visit_priority_ranking":        ("Schedule delegate visits starting with the highest-priority pharmacies.",
                                          "Planifiez les visites en commencant par les pharmacies prioritaires."),
        "delegate_target_achievement":   ("Coach delegates at risk of missing their target this month.",
                                          "Accompagnez les delegues risquant de manquer leur objectif ce mois."),
        "complaint_recurrence_risk":     ("Assign an account manager to high-risk pharmacies.",
                                          "Assignez un responsable compte aux pharmacies a haut risque de plainte."),
        "delegate_activity_drop":        ("Review workload and motivation for delegates showing activity drops.",
                                          "Analysez la charge et la motivation des delegues en baisse d'activite."),
        "pharmacy_next_purchase_date":   ("Schedule delegate contact 3 days before the predicted purchase date.",
                                          "Planifiez un contact delegue 3 jours avant la date d'achat prevue."),
    }

    SYSTEM = """You are a business explanation agent for Medinote, a pharmaceutical CRM.
Convert raw ML prediction results into clear, actionable business insights.
Reply in the SAME language as the original request (French, English, or Arabic).
Rules:
- Lead with the most important finding
- Show top 5 entities with confidence percentages
- For mode2 results state clearly: "This is rule-based analysis, not an AI prediction"
- End with ONE concrete recommended action
- Under 200 words. No technical jargon (no model names, no R2, no AUC)."""

    def __init__(self, api_key: str = ""):
        self._client = _make_llm_client(api_key)

    def explain(self, intent: dict, result: dict) -> str:
        if self._client:
            try:
                user_msg = (
                    f"Original request: {intent['original_request']}\n"
                    f"Task: {result['task_id']} | Mode: {result['mode']}\n"
                    f"Total entities analyzed: {result['total_entities']}\n"
                    f"Top results: {json.dumps(result['results'][:10], ensure_ascii=False)}\n"
                    + (f"Fallback rule: {result.get('fallback_rule','')}\n" if result['mode']=='mode2' else "")
                    + "Write a clear business explanation."
                )
                resp = self._client.chat.completions.create(
                    model=OPENROUTER_MODEL_SMART,
                    max_tokens=400,
                    temperature=0.3,
                    messages=[
                        {"role": "user", "content": self.SYSTEM + "\n\n" + user_msg},
                    ],
                )
                return resp.choices[0].message.content.strip()
            except Exception as exc:
                log.warning("Explanation LLM error (%s) — using template", exc)

        lang = self._detect_lang(intent.get("original_request", ""))
        return self._build(intent, result, lang)

    def _detect_lang(self, text: str) -> str:
        fr_markers = ["quelles", "quels", "quelle", "quel", "est-ce", "sont",
                      "les", "des", "qui", "pour", "notre", "nos", "cette",
                      "comment", "mois", "semaine", "cette semaine", "delegue"]
        score = sum(1 for m in fr_markers if m in text.lower())
        return "fr" if score >= 2 else "en"

    def _build(self, intent: dict, result: dict, lang: str) -> str:
        task_id  = result["task_id"]
        mode     = result["mode"]
        total    = result["total_entities"]
        top      = result["results"][:5]
        idx      = 1 if lang == "fr" else 0

        label  = self._TASK_LABELS.get(task_id, (task_id, task_id))[idx]
        action = self._ACTIONS.get(task_id, ("Review results and take action.",
                                              "Examinez les resultats et agissez."))[idx]

        lines = []

        if mode == "mode2":
            if lang == "fr":
                lines.append(f"[Analyse Regles] {label} — {total} entites analysees.")
                lines.append("Note : Ceci est une analyse basee sur des regles, pas une prediction IA.")
                if result.get("fallback_rule"):
                    lines.append(f"Regle : {result['fallback_rule']}")
            else:
                lines.append(f"[Rule-Based] {label} — {total} entities analyzed.")
                lines.append("Note: This is rule-based analysis, not an AI prediction.")
                if result.get("fallback_rule"):
                    lines.append(f"Rule: {result['fallback_rule']}")
        else:
            task_type = "regression" if any(
                r.get("risk_level") == "value" for r in top
            ) else "classification"

            if lang == "fr":
                lines.append(f"[IA Mode1] {label} — {total} entites analysees.")
                if top:
                    lines.append(f"\nTop {min(5, len(top))} resultats :")
                    for r in top:
                        if task_type == "regression":
                            lines.append(
                                f"  - {r['entity_id']}: {r['score']:,.0f}"
                            )
                        else:
                            lines.append(
                                f"  - {r['entity_id']}: {r['confidence_pct']}% ({r['risk_level']})"
                            )
                else:
                    lines.append("\nAucun resultat disponible.")
            else:
                lines.append(f"[AI Mode1] {label} — {total} entities analyzed.")
                if top:
                    lines.append(f"\nTop {min(5, len(top))} results:")
                    for r in top:
                        if task_type == "regression":
                            lines.append(
                                f"  - {r['entity_id']}: {r['score']:,.0f}"
                            )
                        else:
                            lines.append(
                                f"  - {r['entity_id']}: {r['confidence_pct']}% ({r['risk_level']})"
                            )
                else:
                    lines.append("\nNo results available.")

        lines.append(f"\n=> {action}")
        return "\n".join(lines)


# =============================================================================
# AGENT 0 — OrchestratorAgent
# =============================================================================

class OrchestratorAgent:
    def __init__(self, api_key: str = ""):
        api_key                 = _resolve_api_key(api_key)
        self.db                 = MedinoteDB()
        self.intent_agent       = IntentAgent(api_key)
        self.data_agent         = DataAgent(self.db)
        self.prediction_agent   = PredictionAgent(MODELS_DIR, REGISTRY_PATH)
        self.explanation_agent  = ExplanationAgent(api_key)
        self.capability_checker = CapabilityChecker()
        # Lazy-import to avoid circular dependency
        try:
            from feedback_loop import PredictionLogger
            self._pred_logger = PredictionLogger(self.db)
        except Exception:
            self._pred_logger = None

    def run(self, user_request: str) -> dict:
        ts = datetime.now().isoformat()
        print(f"\n{'='*55}")
        print(f"  [{ts[:19]}] {user_request}")
        print(f"{'='*55}")

        # Step 1: extract intent
        print("Step 1: Extracting intent …")
        intent = self.intent_agent.extract_intent(user_request)
        print(f"  task_id={intent['task_id']}  "
              f"entity_id={intent.get('entity_id')}  "
              f"confidence={intent.get('confidence', 0):.2f}")

        # Step 2: unknown intent -> Mode 3
        if self.intent_agent.is_unknown(intent):
            print("Step 2: Unknown intent -> Mode 3 (logged)")
            self.capability_checker.log_mode3(user_request, "unknown")
            return {
                "status":           "unknown",
                "message":          (
                    "I could not understand this request. "
                    "It has been logged for future development."
                ),
                "original_request": user_request,
            }

        # Step 3: pull features
        print(f"Step 2: Pulling features for {intent['task_id']} …")
        try:
            features = self.data_agent.get_features(intent)
            print(f"  {features.shape[0]} rows x {features.shape[1]} cols")
        except Exception as exc:
            log.error("DataAgent error: %s", exc)
            return {
                "status":  "error",
                "message": f"Could not retrieve data: {exc}",
                "intent":  intent,
            }

        # Step 4: run prediction
        print("Step 3: Running prediction …")
        pred_result = self.prediction_agent.predict(intent["task_id"], features)
        print(f"  mode={pred_result['mode']}  "
              f"entities={pred_result['total_entities']}")

        # Log mode1 predictions to feedback loop
        if pred_result["mode"] == "mode1" and self._pred_logger:
            try:
                self._pred_logger.bulk_log(
                    task_id       = intent["task_id"],
                    results       = pred_result["results"],
                    mode          = pred_result["mode"],
                    model_version = pred_result.get("model_used", ""),
                )
            except Exception as _log_exc:
                log.warning("Prediction logging failed: %s", _log_exc)

        # Step 5: generate explanation
        print("Step 4: Generating explanation …")
        explanation = self.explanation_agent.explain(intent, pred_result)

        final = {
            "status":           "success",
            "request":          user_request,
            "task_id":          intent["task_id"],
            "mode":             pred_result["mode"],
            "total_analyzed":   pred_result["total_entities"],
            "top_results":      pred_result["results"][:10],
            "explanation":      explanation,
            "confidence_note":  self._confidence_note(pred_result),
        }

        print("\nFinal Answer:")
        print(explanation)
        return final

    @staticmethod
    def _confidence_note(result: dict) -> str:
        if result["mode"] == "mode1":
            score = result.get("metric_score", 0) or 0
            return f"AI model confidence: {round(score * 100, 1)}%"
        return "Rule-based analysis — no statistical confidence"

    def close(self):
        self.db.close()


# =============================================================================
# MAIN TEST
# =============================================================================

if __name__ == "__main__":
    API_KEY = _resolve_api_key()
    if not API_KEY:
        print("WARNING: No API key found — LLM steps will use template fallback")
    else:
        print(f"API key loaded (length={len(API_KEY)})")

    orchestrator = OrchestratorAgent(api_key=API_KEY)

    test_requests = [
        "Which pharmacies are about to churn?",
        "Show me the best performing delegates",
        "Which products will have high demand next month?",
        "What is the payment default risk for our clients?",
        "Which pharmacies should I visit first this week?",
        "Show me the weather forecast for Tunis",
    ]

    results = []
    for request in test_requests:
        result = orchestrator.run(request)
        results.append({
            "request":             request,
            "status":              result["status"],
            "task_id":             result.get("task_id", "unknown"),
            "mode":                result.get("mode", "none"),
            "explanation_preview": result.get("explanation", "")[:120],
        })

    print("\n" + "=" * 55)
    print("FULL TEST SUMMARY:")
    print(json.dumps(results, indent=2, ensure_ascii=False))

    orchestrator.close()
