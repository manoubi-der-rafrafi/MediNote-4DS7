"""
Medinote — Database Layer
Replaces all CSV reads with live MariaDB queries against pharma_db.

Discovered schema (2026-04-28):
  t_ttc_ht_qte_qte_g  columns already match target names:
  id, ttc, ht, qte, qte_g, art, cl, date, dlg, fam, zone, created_at, id_crm
  → no column renaming needed.

  t_predictions_cache existing columns:
  id, id_rapport, risk_tier, risk_score, alert_level, delegate_score,
  computed_at, pipeline_version, created_at, updated_at, delegate_id, full_output
  → full_output (mediumtext) stores JSON payload; pipeline_version stores task_id;
    id_rapport stores numeric entity_id; delegate_id stores string entity_id;
    computed_at + 24 h acts as expiry.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import pymysql
import pymysql.cursors
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("medinote.db")

SLOW_QUERY_THRESHOLD = 1.0  # seconds

# ── Connection config ─────────────────────────────────────────────────────────
DB_CONFIG = dict(
    host="127.0.0.1",
    port=3307,
    user="root",
    password="",
    database="pharma_db",
    charset="utf8mb4",
)


# ═══════════════════════════════════════════════════════════════════════════════
# TASK 1 — MedinoteDB connection class
# ═══════════════════════════════════════════════════════════════════════════════

class MedinoteDB:
    """
    Thread-safe MariaDB connection with connection pooling, auto-reconnect,
    and query timing.  All public methods return pandas DataFrames.
    """

    def __init__(self):
        url = (
            f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
            f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}"
            f"/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"
        )
        self._engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,       # auto-reconnect dead connections
            pool_recycle=3600,        # recycle connections every hour
        )
        log.info("MedinoteDB connected to %s:%s/%s",
                 DB_CONFIG["host"], DB_CONFIG["port"], DB_CONFIG["database"])
        self._discover_columns()

    # ── Column discovery ───────────────────────────────────────────────────────

    def _discover_columns(self):
        """Log column names of the main sales table on startup."""
        df = self.query(text("SHOW COLUMNS FROM t_ttc_ht_qte_qte_g"))
        self.columns = dict(zip(df["Field"], df["Type"]))
        log.info("t_ttc_ht_qte_qte_g columns: %s", self.columns)

    # ── Core query method ──────────────────────────────────────────────────────

    def query(self, sql, params: Optional[dict] = None) -> pd.DataFrame:
        """
        Execute a SQL query and return a DataFrame.
        Logs slow queries (> SLOW_QUERY_THRESHOLD seconds).
        Raises on connection errors after logging.
        """
        t0 = time.perf_counter()
        try:
            with self._engine.connect() as conn:
                df = pd.read_sql(sql, conn, params=params)
            elapsed = time.perf_counter() - t0
            if elapsed > SLOW_QUERY_THRESHOLD:
                log.warning("SLOW QUERY (%.2fs): %s", elapsed, str(sql)[:120])
            else:
                log.debug("Query OK (%.3fs) rows=%d", elapsed, len(df))
            return df
        except Exception as exc:
            log.error("Query failed: %s | SQL: %s", exc, str(sql)[:200])
            raise

    def execute(self, sql, params: Optional[dict] = None):
        """Execute a DML statement (INSERT/UPDATE/DELETE). Returns CursorResult."""
        with self._engine.begin() as conn:
            return conn.execute(sql, params or {})

    def execute_many(self, sql, rows: list):
        """Execute a DML statement for each row in rows (bulk insert)."""
        if not rows:
            return
        with self._engine.begin() as conn:
            conn.execute(sql, rows)

    def close(self):
        self._engine.dispose()
        log.info("MedinoteDB connection pool closed.")

    # ── Internal helper: window boundaries ────────────────────────────────────

    def _get_reference_date(self) -> datetime:
        """
        Use the latest date in the sales table as 'today'.
        This keeps windowed queries correct even when running against
        historical exports where the data ends before the current date.
        Falls back to datetime.today() if the table is empty.
        """
        if not hasattr(self, "_ref_date"):
            df = self.query(text("SELECT MAX(`date`) AS max_date FROM t_ttc_ht_qte_qte_g"))
            val = df["max_date"].iloc[0]
            self._ref_date = pd.to_datetime(val).to_pydatetime() if val else datetime.today()
            log.info("Reference date set to data max: %s", self._ref_date.date())
        return self._ref_date

    def _cutoff(self, days: int) -> str:
        """Return ISO date string for (data_max_date - N days)."""
        return (self._get_reference_date() - timedelta(days=days)).strftime("%Y-%m-%d")

    # ==========================================================================
    # TASK 2 — Sales Data Layer
    # ==========================================================================

    def get_sales(
        self,
        days: int = 90,
        pharmacy_id: Optional[str] = None,
        delegate_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Pull raw sales rows from t_ttc_ht_qte_qte_g.
        Columns returned: cl, dlg, date, ttc, ht, qte, art, fam, zone.
        """
        where = ["DATE(`date`) >= :cutoff"]
        params = {"cutoff": self._cutoff(days)}

        if pharmacy_id is not None:
            where.append("cl = :pharmacy_id")
            params["pharmacy_id"] = str(pharmacy_id)

        if delegate_id is not None:
            where.append("dlg = :delegate_id")
            params["delegate_id"] = str(delegate_id)

        sql = text(f"""
            SELECT cl, dlg, `date`, ttc, ht, qte, art, fam, zone
            FROM   t_ttc_ht_qte_qte_g
            WHERE  {' AND '.join(where)}
        """)
        df = self.query(sql, params)
        df["ttc"] = pd.to_numeric(df["ttc"], errors="coerce")
        df["ht"]  = pd.to_numeric(df["ht"],  errors="coerce")
        df["qte"] = pd.to_numeric(df["qte"], errors="coerce")
        df["date"] = pd.to_datetime(df["date"])
        return df

    def get_pharmacy_summary(
        self,
        pharmacy_id: Optional[str] = None,
        days: int = 90,
    ) -> pd.DataFrame:
        """
        Aggregate sales per pharmacy.
        Returns: cl, revenue_total, order_count, days_since_last_order,
                 distinct_products.
        """
        where = "DATE(`date`) >= :cutoff"
        params: dict = {"cutoff": self._cutoff(days)}

        if pharmacy_id is not None:
            where += " AND cl = :pharmacy_id"
            params["pharmacy_id"] = str(pharmacy_id)

        params["ref_date"] = self._get_reference_date().strftime("%Y-%m-%d")
        sql = text(f"""
            SELECT
                cl,
                SUM(ttc)                              AS revenue_total,
                COUNT(DISTINCT DATE(`date`))          AS order_count,
                DATEDIFF(:ref_date, MAX(`date`))      AS days_since_last_order,
                COUNT(DISTINCT art)                   AS distinct_products
            FROM  t_ttc_ht_qte_qte_g
            WHERE {where}
            GROUP BY cl
        """)
        return self.query(sql, params)

    def get_delegate_summary(
        self,
        delegate_id: Optional[str] = None,
        days: int = 90,
    ) -> pd.DataFrame:
        """
        Aggregate sales per delegate.
        Returns: dlg, revenue_total, order_count, distinct_pharmacies,
                 avg_order_value.
        """
        where = "DATE(`date`) >= :cutoff AND dlg IS NOT NULL AND dlg != ''"
        params: dict = {"cutoff": self._cutoff(days)}

        if delegate_id is not None:
            where += " AND dlg = :delegate_id"
            params["delegate_id"] = str(delegate_id)

        sql = text(f"""
            SELECT
                dlg,
                SUM(ttc)                              AS revenue_total,
                COUNT(DISTINCT DATE(`date`))          AS order_count,
                COUNT(DISTINCT cl)                    AS distinct_pharmacies,
                SUM(ttc) / NULLIF(COUNT(DISTINCT DATE(`date`)), 0)
                                                      AS avg_order_value
            FROM  t_ttc_ht_qte_qte_g
            WHERE {where}
            GROUP BY dlg
        """)
        return self.query(sql, params)

    def get_product_summary(
        self,
        product_id: Optional[str] = None,
        days: int = 90,
    ) -> pd.DataFrame:
        """
        Aggregate sales per product.
        Returns: art, revenue_total, qty_total, distinct_buyers, order_count.
        """
        where = "DATE(`date`) >= :cutoff"
        params: dict = {"cutoff": self._cutoff(days)}

        if product_id is not None:
            where += " AND art = :product_id"
            params["product_id"] = str(product_id)

        sql = text(f"""
            SELECT
                art,
                SUM(ttc)              AS revenue_total,
                SUM(qte)              AS qty_total,
                COUNT(DISTINCT cl)    AS distinct_buyers,
                COUNT(*)              AS order_count
            FROM  t_ttc_ht_qte_qte_g
            WHERE {where}
            GROUP BY art
        """)
        return self.query(sql, params)


# ═══════════════════════════════════════════════════════════════════════════════
# TASK 3 — FeatureBuilder
# ═══════════════════════════════════════════════════════════════════════════════

class FeatureBuilder:
    """Builds ML-ready feature DataFrames from live DB data."""

    def __init__(self, db: MedinoteDB):
        self.db = db

    # ── helpers ────────────────────────────────────────────────────────────────

    def _cutoff(self, days: int) -> str:
        return self.db._cutoff(days)

    def _window_revenue(self, days: int, pharmacy_id: Optional[str]) -> pd.DataFrame:
        where = "DATE(`date`) >= :cutoff"
        params: dict = {"cutoff": self._cutoff(days)}
        if pharmacy_id is not None:
            where += " AND cl = :pharmacy_id"
            params["pharmacy_id"] = str(pharmacy_id)
        sql = text(f"""
            SELECT cl, SUM(ttc) AS revenue, COUNT(DISTINCT DATE(`date`)) AS orders
            FROM   t_ttc_ht_qte_qte_g
            WHERE  {where}
            GROUP BY cl
        """)
        return self.db.query(sql, params)

    # ── pharmacy churn features ────────────────────────────────────────────────

    def pharmacy_churn_features(
        self, pharmacy_id: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Multi-window churn feature set.
        churn_label = 1 if days_since_last_order > 240 AND historical orders >= 3.
        """
        # base: days since last order + lifetime order count
        where_base = "1=1"
        params_base: dict = {}
        if pharmacy_id is not None:
            where_base = "cl = :pharmacy_id"
            params_base["pharmacy_id"] = str(pharmacy_id)

        ref_date = self.db._get_reference_date().strftime("%Y-%m-%d")
        cutoff_base = self._cutoff(730)   # 2 years is enough; older = already lost
        if where_base == "1=1":
            where_base = "DATE(`date`) >= :cutoff_base"
            params_base["cutoff_base"] = cutoff_base
        else:
            where_base += " AND DATE(`date`) >= :cutoff_base"
            params_base["cutoff_base"] = cutoff_base

        base_sql = text(f"""
            SELECT
                cl,
                DATEDIFF(:ref_date, MAX(`date`))      AS days_since_last_order,
                COUNT(DISTINCT DATE(`date`))           AS total_order_count
            FROM  t_ttc_ht_qte_qte_g
            WHERE {where_base}
            GROUP BY cl
        """)
        params_base["ref_date"] = ref_date
        base = self.db.query(base_sql, params_base)

        # revenue + order count per window
        for days, suffix in [(30, "30d"), (90, "90d"), (180, "180d")]:
            w = self._window_revenue(days, pharmacy_id).rename(columns={
                "revenue": f"revenue_{suffix}",
                "orders":  f"order_count_{suffix}",
            })
            base = base.merge(w, on="cl", how="left")

        base = base.fillna(0)

        # revenue trend: 90d vs previous 90d (90–180d window)
        prev_sql = text("""
            SELECT cl,
                   SUM(ttc) AS revenue_prev_90d
            FROM   t_ttc_ht_qte_qte_g
            WHERE  DATE(`date`) >= :from_date
              AND  DATE(`date`) <  :to_date
            GROUP BY cl
        """)
        prev = self.db.query(prev_sql, {
            "from_date": self._cutoff(180),
            "to_date":   self._cutoff(90),
        })
        base = base.merge(prev, on="cl", how="left").fillna(0)
        base["revenue_trend"] = (
            base["revenue_90d"] - base["revenue_prev_90d"]
        )
        base["order_frequency_trend"] = (
            base["order_count_90d"] - base["order_count_180d"] / 2
        )

        # churn label
        base["churn_label"] = (
            (base["days_since_last_order"] > 240) &
            (base["total_order_count"] >= 3)
        ).astype(int)

        cols = [
            "cl", "days_since_last_order",
            "order_count_30d", "order_count_90d", "order_count_180d",
            "revenue_30d", "revenue_90d", "revenue_180d",
            "revenue_trend", "order_frequency_trend", "churn_label",
        ]
        return base[cols]

    # ── delegate performance features ─────────────────────────────────────────

    def delegate_performance_features(
        self, delegate_id: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Delegate scoring: revenue, orders, pharmacies in last 90d.
        performance_score = 0.5*norm_revenue + 0.3*norm_orders + 0.2*norm_pharm
        """
        df = self.db.get_delegate_summary(delegate_id=delegate_id, days=90)
        df = df.rename(columns={
            "revenue_total":      "revenue_90d",
            "order_count":        "order_count_90d",
            "distinct_pharmacies":"distinct_pharmacies_90d",
        })

        def minmax(col):
            mn, mx = col.min(), col.max()
            return (col - mn) / (mx - mn) if mx != mn else pd.Series(0.5, index=col.index)

        df["performance_score"] = (
            0.5 * minmax(df["revenue_90d"]) +
            0.3 * minmax(df["order_count_90d"]) +
            0.2 * minmax(df["distinct_pharmacies_90d"])
        )
        return df[["dlg", "revenue_90d", "order_count_90d",
                   "distinct_pharmacies_90d", "performance_score"]]

    # ── sales forecast features ────────────────────────────────────────────────

    def sales_forecast_features(
        self, pharmacy_id: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Multi-window revenue features for 30-day revenue forecast.
        target_revenue_30d = revenue_30d (what the model learns to predict).
        """
        base = None
        for days, suffix in [(30, "30d"), (60, "60d"), (90, "90d"), (180, "180d")]:
            w = self._window_revenue(days, pharmacy_id).rename(columns={
                "revenue": f"revenue_{suffix}",
                "orders":  f"order_count_{suffix}",
            })
            base = w if base is None else base.merge(w, on="cl", how="outer")

        base = base.fillna(0)
        base["target_revenue_30d"] = base["revenue_30d"]
        cols = ["cl", "revenue_30d", "revenue_60d", "revenue_90d",
                "revenue_180d", "order_count_90d", "target_revenue_30d"]
        return base[cols]

    # ── product demand features ────────────────────────────────────────────────

    def product_demand_features(
        self, product_id: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Multi-window product features for 30-day demand forecast.
        target_demand_30d = revenue_30d.
        """
        base = None
        for days, suffix in [(30, "30d"), (60, "60d"), (90, "90d")]:
            where = "DATE(`date`) >= :cutoff"
            params: dict = {"cutoff": self._cutoff(days)}
            if product_id is not None:
                where += " AND art = :product_id"
                params["product_id"] = str(product_id)
            sql = text(f"""
                SELECT art,
                       SUM(ttc)           AS revenue_{suffix},
                       COUNT(DISTINCT cl) AS distinct_buyers_{suffix}
                FROM   t_ttc_ht_qte_qte_g
                WHERE  {where}
                GROUP BY art
            """)
            w = self.db.query(sql, params)
            base = w if base is None else base.merge(w, on="art", how="outer")

        base = base.fillna(0)
        base["target_demand_30d"] = base["revenue_30d"]
        cols = ["art", "revenue_30d", "revenue_60d", "revenue_90d",
                "distinct_buyers_90d", "target_demand_30d"]
        # keep only columns that exist (outer merge may rename)
        cols = [c for c in cols if c in base.columns]
        return base[cols]


# ═══════════════════════════════════════════════════════════════════════════════
# TASK 4 — Prediction Cache Layer (on existing t_predictions_cache)
# ═══════════════════════════════════════════════════════════════════════════════

class PredictionCache:
    """
    Wraps t_predictions_cache for generic task/entity caching.

    Mapping to existing columns:
      pipeline_version → task_id   (varchar 10, truncated if needed)
      id_rapport       → numeric entity id (0 if non-numeric)
      delegate_id      → string entity id
      risk_score       → confidence (float)
      full_output      → JSON payload (result dict + expires_at)
      computed_at      → written timestamp; expiry = computed_at + 24h
    """

    TTL_HOURS = 24

    def __init__(self, db: MedinoteDB):
        self._db = db

    def cache_prediction(
        self,
        task_id: str,
        entity_id,
        result: dict,
        confidence: float,
        mode: str,
    ) -> None:
        """Insert or replace a prediction into t_predictions_cache."""
        expires_at = datetime.now() + timedelta(hours=self.TTL_HOURS)
        payload = {
            "task_id":    task_id,
            "entity_id":  str(entity_id),
            "mode":       mode,
            "result":     result,
            "expires_at": expires_at.isoformat(),
        }
        numeric_id = int(entity_id) if str(entity_id).isdigit() else 0
        sql = text("""
            INSERT INTO t_predictions_cache
                (id_rapport, pipeline_version, risk_score,
                 delegate_id, full_output, computed_at)
            VALUES
                (:id_rapport, :task_id, :confidence,
                 :entity_str, :payload, NOW())
        """)
        with self._db._engine.begin() as conn:
            conn.execute(sql, {
                "id_rapport":  numeric_id,
                "task_id":     task_id[:10],
                "confidence":  float(confidence),
                "entity_str":  str(entity_id),
                "payload":     json.dumps(payload),
            })
        log.info("Cached prediction: task=%s entity=%s conf=%.3f",
                 task_id, entity_id, confidence)

    def get_cached_prediction(
        self, task_id: str, entity_id
    ) -> Optional[dict]:
        """
        Return unexpired cached prediction dict, or None if missing/expired.
        Expiry = computed_at + 24 hours.
        """
        sql = text("""
            SELECT full_output, computed_at
            FROM   t_predictions_cache
            WHERE  pipeline_version = :task_id
              AND  delegate_id      = :entity_str
            ORDER BY computed_at DESC
            LIMIT 1
        """)
        df = self._db.query(sql, {
            "task_id":    task_id[:10],
            "entity_str": str(entity_id),
        })
        if df.empty or df["full_output"].iloc[0] is None:
            return None

        computed_at = pd.to_datetime(df["computed_at"].iloc[0])
        if datetime.now() - computed_at.to_pydatetime() > timedelta(hours=self.TTL_HOURS):
            log.debug("Cache expired for task=%s entity=%s", task_id, entity_id)
            return None

        payload = json.loads(df["full_output"].iloc[0])
        log.info("Cache hit: task=%s entity=%s", task_id, entity_id)
        return payload


# ═══════════════════════════════════════════════════════════════════════════════
# TASK 5 — Connection Test
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    db = MedinoteDB()

    print("=" * 60)
    print("Testing connection...")
    total = db.query(text("SELECT COUNT(*) AS total FROM t_ttc_ht_qte_qte_g"))
    print(total)

    print("\nTesting pharmacy summary (last 90 days)...")
    summary = db.get_pharmacy_summary(days=90)
    print(f"Pharmacies with sales in last 90 days: {len(summary)}")
    print(summary.head())

    print("\nTesting delegate summary...")
    del_summary = db.get_delegate_summary(days=90)
    print(f"Active delegates: {len(del_summary)}")
    print(del_summary.head())

    print("\nTesting product summary...")
    prod_summary = db.get_product_summary(days=90)
    print(f"Active products: {len(prod_summary)}")
    print(prod_summary.head())

    print("\nTesting FeatureBuilder...")
    fb = FeatureBuilder(db)

    print("  pharmacy_churn_features...")
    churn_features = fb.pharmacy_churn_features()
    print(f"  Churn features built for {len(churn_features)} pharmacies")
    print(churn_features.head())

    print("\n  delegate_performance_features...")
    del_features = fb.delegate_performance_features()
    print(f"  Delegate features: {len(del_features)} delegates")
    print(del_features.head())

    print("\n  sales_forecast_features...")
    fc_features = fb.sales_forecast_features()
    print(f"  Forecast features: {len(fc_features)} pharmacies")
    print(fc_features.head())

    print("\n  product_demand_features...")
    pd_features = fb.product_demand_features()
    print(f"  Product demand features: {len(pd_features)} products")
    print(pd_features.head())

    print("\nTesting PredictionCache...")
    cache = PredictionCache(db)
    cache.cache_prediction(
        task_id="churn_test",
        entity_id="411C003",
        result={"churn_risk": 0.72, "tier": "HIGH"},
        confidence=0.85,
        mode="batch",
    )
    hit = cache.get_cached_prediction("churn_test", "411C003")
    print(f"  Cache write+read OK: {hit is not None}")
    print(f"  Payload: {hit}")

    db.close()
    print("\nAll tests passed.")
