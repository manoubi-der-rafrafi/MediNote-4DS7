"""
Medinote Feedback Loop — prediction logging, outcome validation,
drift detection, and retraining triggers.

Usage:
  python feedback_loop.py --mode health      # show model health table
  python feedback_loop.py --mode validate    # run validation now
  python feedback_loop.py --mode scheduler   # start background scheduler
  python feedback_loop.py --mode queue       # show retraining queue
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

sys.path.insert(0, r"c:\Users\omri\Desktop\pii")
from db_layer import MedinoteDB, FeatureBuilder

log = logging.getLogger("medinote.feedback")

REGISTRY_PATH   = r"c:\Users\omri\Desktop\pii\models\model_registry.json"
QUEUE_PATH      = r"c:\Users\omri\Desktop\pii\retraining_queue.json"
DRIFT_THRESHOLD = 0.10   # 10% precision drop triggers retraining

# Validation windows per task (days)
VALIDATE_WINDOWS = {
    "pharmacy_churn_risk":          60,
    "payment_default_risk":         30,
    "order_cancellation_risk":      14,
    "pharmacy_tier_upgrade":        90,
    "product_demand_forecast":      30,
    "campaign_response_probability":14,
    "product_sales_trend":          30,
    "delegate_performance_score":   90,
    "default":                      30,
}

# Tasks that support outcome validation
VALIDATABLE_TASKS = {
    "pharmacy_churn_risk",
    "payment_default_risk",
    "order_cancellation_risk",
    "pharmacy_tier_upgrade",
    "product_sales_trend",
    "campaign_response_probability",
}


# =============================================================================
# COMPONENT 1 — Prediction Logger
# =============================================================================

class PredictionLogger:
    def __init__(self, db: MedinoteDB):
        self.db = db
        self._ensure_table()

    def _ensure_table(self):
        self.db.execute(text("""
            CREATE TABLE IF NOT EXISTS t_prediction_log (
                id              INT AUTO_INCREMENT PRIMARY KEY,
                task_id         VARCHAR(100)  NOT NULL,
                entity_id       VARCHAR(150)  NOT NULL,
                prediction_score FLOAT        NOT NULL,
                risk_level      VARCHAR(20)   NOT NULL,
                mode            VARCHAR(20)   NOT NULL,
                model_version   VARCHAR(150)  NOT NULL,
                predicted_at    DATETIME      NOT NULL,
                validate_after  DATETIME      NOT NULL,
                actual_outcome  INT           DEFAULT NULL,
                validated_at    DATETIME      DEFAULT NULL,
                was_correct     INT           DEFAULT NULL,
                INDEX idx_task_validate (task_id, validate_after),
                INDEX idx_entity (task_id, entity_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))

    def log_prediction(self,
                       task_id: str,
                       entity_id: str,
                       score: float,
                       risk_level: str,
                       mode: str,
                       model_version: str,
                       validate_after_days: int = 30) -> int:
        now            = datetime.now(timezone.utc).replace(tzinfo=None)
        validate_after = now + timedelta(days=validate_after_days)
        result = self.db.execute(text("""
            INSERT INTO t_prediction_log
                (task_id, entity_id, prediction_score, risk_level,
                 mode, model_version, predicted_at, validate_after)
            VALUES
                (:task_id, :entity_id, :score, :risk_level,
                 :mode, :model_version, :predicted_at, :validate_after)
        """), {
            "task_id":        task_id,
            "entity_id":      str(entity_id),
            "score":          float(score),
            "risk_level":     risk_level,
            "mode":           mode,
            "model_version":  model_version,
            "predicted_at":   now,
            "validate_after": validate_after,
        })
        return result.lastrowid

    def bulk_log(self,
                 task_id: str,
                 results: list,
                 mode: str,
                 model_version: str):
        if not results:
            return
        window = VALIDATE_WINDOWS.get(task_id, VALIDATE_WINDOWS["default"])
        now    = datetime.now(timezone.utc).replace(tzinfo=None)
        va     = now + timedelta(days=window)

        rows = [
            {
                "task_id":        task_id,
                "entity_id":      str(r["entity_id"]),
                "score":          float(r["score"]),
                "risk_level":     r.get("risk_level", "MEDIUM"),
                "mode":           mode,
                "model_version":  model_version,
                "predicted_at":   now,
                "validate_after": va,
            }
            for r in results
        ]

        self.db.execute_many(text("""
            INSERT INTO t_prediction_log
                (task_id, entity_id, prediction_score, risk_level,
                 mode, model_version, predicted_at, validate_after)
            VALUES
                (:task_id, :entity_id, :score, :risk_level,
                 :mode, :model_version, :predicted_at, :validate_after)
        """), rows)
        log.info("Logged %d predictions for %s", len(rows), task_id)


# =============================================================================
# COMPONENT 2 — Outcome Validator
# =============================================================================

class OutcomeValidator:
    def __init__(self, db: MedinoteDB):
        self.db = db
        self.fb = FeatureBuilder(db)

    def validate_due_predictions(self) -> dict:
        due = self.db.query(text("""
            SELECT id, task_id, entity_id, prediction_score,
                   risk_level, predicted_at
            FROM   t_prediction_log
            WHERE  validate_after <= NOW()
              AND  actual_outcome IS NULL
              AND  task_id IN :tasks
            ORDER  BY predicted_at
            LIMIT  500
        """), {"tasks": tuple(VALIDATABLE_TASKS)})

        if due.empty:
            log.info("No predictions due for validation")
            return {"validated": 0, "correct": 0, "incorrect": 0,
                    "precision": None, "by_task": {}}

        validated = correct = incorrect = 0
        by_task: dict = {}

        for _, row in due.iterrows():
            task_id    = row["task_id"]
            entity_id  = row["entity_id"]
            score      = float(row["prediction_score"])
            risk_level = row["risk_level"]
            predicted_at = str(row["predicted_at"])[:10]

            outcome = self._get_actual_outcome(task_id, entity_id, predicted_at)
            if outcome is None:
                continue

            # was_correct: prediction said HIGH risk → did bad thing happen?
            predicted_positive = risk_level in ("HIGH", "CRITICAL") or score >= 0.5
            was_correct = int(predicted_positive == bool(outcome))

            self.db.execute(text("""
                UPDATE t_prediction_log
                SET    actual_outcome = :outcome,
                       validated_at   = NOW(),
                       was_correct    = :was_correct
                WHERE  id = :id
            """), {"outcome": outcome, "was_correct": was_correct, "id": int(row["id"])})

            validated += 1
            if was_correct:
                correct += 1
            else:
                incorrect += 1

            if task_id not in by_task:
                by_task[task_id] = {"validated": 0, "correct": 0}
            by_task[task_id]["validated"] += 1
            by_task[task_id]["correct"]   += was_correct

        precision = round(correct / validated, 4) if validated else None
        for t, v in by_task.items():
            v["precision"] = round(v["correct"] / v["validated"], 4) if v["validated"] else None

        log.info("Validation done: %d validated, precision=%.3f",
                 validated, precision or 0)
        return {
            "validated": validated,
            "correct":   correct,
            "incorrect": incorrect,
            "precision": precision,
            "by_task":   by_task,
        }

    def _get_actual_outcome(self, task_id: str, entity_id: str,
                            predicted_at: str) -> int | None:
        handlers = {
            "pharmacy_churn_risk":           self._churn_outcome,
            "payment_default_risk":          self._payment_outcome,
            "order_cancellation_risk":       self._cancel_outcome,
            "pharmacy_tier_upgrade":         self._tier_outcome,
            "product_sales_trend":           self._trend_outcome,
            "campaign_response_probability": self._campaign_outcome,
        }
        handler = handlers.get(task_id)
        if handler is None:
            return None
        try:
            return handler(entity_id, predicted_at)
        except Exception as exc:
            log.warning("Outcome check failed for %s/%s: %s", task_id, entity_id, exc)
            return None

    # ── Individual outcome checkers ────────────────────────────────────────────

    def _churn_outcome(self, pharmacy_id: str, predicted_at: str) -> int:
        """1 = churned (no orders in 60d), 0 = stayed active."""
        df = self.db.query(text("""
            SELECT COUNT(*) AS order_count
            FROM   t_ttc_ht_qte_qte_g
            WHERE  cl = :pid
              AND  DATE(`date`) >  :dt
              AND  DATE(`date`) <= DATE_ADD(:dt, INTERVAL 60 DAY)
        """), {"pid": pharmacy_id, "dt": predicted_at})
        return 1 if int(df.iloc[0]["order_count"]) == 0 else 0

    def _payment_outcome(self, pharmacy_id: str, predicted_at: str) -> int:
        """1 = payment issue (orders dropped >50% in 30d after vs 30d before)."""
        before = self.db.query(text("""
            SELECT COUNT(DISTINCT DATE(`date`)) AS cnt
            FROM   t_ttc_ht_qte_qte_g
            WHERE  cl = :pid
              AND  DATE(`date`) >= DATE_SUB(:dt, INTERVAL 30 DAY)
              AND  DATE(`date`) <  :dt
        """), {"pid": pharmacy_id, "dt": predicted_at})
        after = self.db.query(text("""
            SELECT COUNT(DISTINCT DATE(`date`)) AS cnt
            FROM   t_ttc_ht_qte_qte_g
            WHERE  cl = :pid
              AND  DATE(`date`) >  :dt
              AND  DATE(`date`) <= DATE_ADD(:dt, INTERVAL 30 DAY)
        """), {"pid": pharmacy_id, "dt": predicted_at})
        cnt_before = int(before.iloc[0]["cnt"])
        cnt_after  = int(after.iloc[0]["cnt"])
        if cnt_before == 0:
            return 0
        return 1 if (cnt_before - cnt_after) / cnt_before > 0.50 else 0

    def _cancel_outcome(self, pharmacy_id: str, predicted_at: str) -> int:
        """1 = significant drop in orders in 14d after prediction."""
        before = self.db.query(text("""
            SELECT COUNT(DISTINCT DATE(`date`)) AS cnt
            FROM   t_ttc_ht_qte_qte_g
            WHERE  cl = :pid
              AND  DATE(`date`) >= DATE_SUB(:dt, INTERVAL 14 DAY)
              AND  DATE(`date`) <  :dt
        """), {"pid": pharmacy_id, "dt": predicted_at})
        after = self.db.query(text("""
            SELECT COUNT(DISTINCT DATE(`date`)) AS cnt
            FROM   t_ttc_ht_qte_qte_g
            WHERE  cl = :pid
              AND  DATE(`date`) >  :dt
              AND  DATE(`date`) <= DATE_ADD(:dt, INTERVAL 14 DAY)
        """), {"pid": pharmacy_id, "dt": predicted_at})
        cnt_before = int(before.iloc[0]["cnt"])
        cnt_after  = int(after.iloc[0]["cnt"])
        if cnt_before == 0:
            return 1   # was already inactive
        return 1 if cnt_after < cnt_before * 0.5 else 0

    def _tier_outcome(self, pharmacy_id: str, predicted_at: str) -> int:
        """1 = revenue grew >20% in 90d after vs 90d before."""
        before = self.db.query(text("""
            SELECT COALESCE(SUM(ttc), 0) AS rev
            FROM   t_ttc_ht_qte_qte_g
            WHERE  cl = :pid
              AND  DATE(`date`) >= DATE_SUB(:dt, INTERVAL 90 DAY)
              AND  DATE(`date`) <  :dt
        """), {"pid": pharmacy_id, "dt": predicted_at})
        after = self.db.query(text("""
            SELECT COALESCE(SUM(ttc), 0) AS rev
            FROM   t_ttc_ht_qte_qte_g
            WHERE  cl = :pid
              AND  DATE(`date`) >  :dt
              AND  DATE(`date`) <= DATE_ADD(:dt, INTERVAL 90 DAY)
        """), {"pid": pharmacy_id, "dt": predicted_at})
        rev_before = float(before.iloc[0]["rev"])
        rev_after  = float(after.iloc[0]["rev"])
        if rev_before == 0:
            return 1 if rev_after > 0 else 0
        return 1 if (rev_after - rev_before) / rev_before > 0.20 else 0

    def _trend_outcome(self, product_id: str, predicted_at: str) -> int:
        """1 = product revenue lower in 30d after vs 30d before (downtrend confirmed)."""
        before = self.db.query(text("""
            SELECT COALESCE(SUM(ttc), 0) AS rev
            FROM   t_ttc_ht_qte_qte_g
            WHERE  art = :pid
              AND  DATE(`date`) >= DATE_SUB(:dt, INTERVAL 30 DAY)
              AND  DATE(`date`) <  :dt
        """), {"pid": product_id, "dt": predicted_at})
        after = self.db.query(text("""
            SELECT COALESCE(SUM(ttc), 0) AS rev
            FROM   t_ttc_ht_qte_qte_g
            WHERE  art = :pid
              AND  DATE(`date`) >  :dt
              AND  DATE(`date`) <= DATE_ADD(:dt, INTERVAL 30 DAY)
        """), {"pid": product_id, "dt": predicted_at})
        return 1 if float(after.iloc[0]["rev"]) < float(before.iloc[0]["rev"]) else 0

    def _campaign_outcome(self, pharmacy_id: str, predicted_at: str) -> int:
        """1 = pharmacy placed an order in 14d after prediction."""
        df = self.db.query(text("""
            SELECT COUNT(*) AS cnt
            FROM   t_ttc_ht_qte_qte_g
            WHERE  cl = :pid
              AND  DATE(`date`) >  :dt
              AND  DATE(`date`) <= DATE_ADD(:dt, INTERVAL 14 DAY)
        """), {"pid": pharmacy_id, "dt": predicted_at})
        return 1 if int(df.iloc[0]["cnt"]) > 0 else 0


# =============================================================================
# COMPONENT 3 — Model Health Monitor
# =============================================================================

class ModelHealthMonitor:
    def __init__(self, db: MedinoteDB, registry_path: str):
        self.db            = db
        self.registry_path = registry_path
        self._registry     = self._load_registry()

    def _load_registry(self) -> dict:
        with open(self.registry_path, encoding="utf-8") as f:
            return json.load(f)

    def _baseline_precision(self, task_id: str) -> float:
        """Extract best precision proxy from registry."""
        task = self._registry.get(task_id, {})
        for key in ("baseline_precision", "honest_auc", "baseline_auc", "baseline_r2"):
            val = task.get(key)
            if val is not None and val > 0:
                return float(val)
        return 0.5   # default if nothing found

    def get_model_health(self, task_id: str) -> dict:
        df = self.db.query(text("""
            SELECT
                COUNT(*)                                        AS total,
                COALESCE(SUM(CASE WHEN was_correct IS NOT NULL
                                  THEN 1 ELSE 0 END), 0)        AS validated,
                COALESCE(SUM(CASE WHEN was_correct = 1
                                  THEN 1 ELSE 0 END), 0)        AS correct
            FROM t_prediction_log
            WHERE task_id = :task_id
        """), {"task_id": task_id})

        row        = df.iloc[0]
        total      = int(row["total"])
        validated  = int(row["validated"])
        correct    = int(row["correct"])

        real_prec  = round(correct / validated, 4) if validated > 0 else None
        baseline   = self._baseline_precision(task_id)
        drift      = round(baseline - real_prec, 4) if real_prec is not None else None

        if real_prec is None:
            status = "NO_DATA"
            rec    = "Insufficient validated predictions — wait for validation window."
        elif drift is not None and drift >= DRIFT_THRESHOLD:
            status = "CRITICAL"
            rec    = f"Precision dropped {drift*100:.1f}% below baseline — retrain immediately."
        elif drift is not None and drift >= DRIFT_THRESHOLD / 2:
            status = "WARNING"
            rec    = f"Precision drifting ({drift*100:.1f}% below baseline) — monitor closely."
        else:
            status = "GOOD"
            rec    = "Model performing within expected range."

        registry_mode = self._registry.get(task_id, {}).get("mode_active", "?")

        return {
            "task_id":           task_id,
            "mode":              registry_mode,
            "total_predictions": total,
            "validated_count":   validated,
            "real_precision":    real_prec,
            "baseline_precision":baseline,
            "drift":             drift,
            "health_status":     status,
            "recommendation":    rec,
        }

    def check_drift(self, task_id: str) -> bool:
        """True if last 100 validated predictions drift > threshold."""
        df = self.db.query(text("""
            SELECT was_correct
            FROM   t_prediction_log
            WHERE  task_id    = :task_id
              AND  was_correct IS NOT NULL
            ORDER  BY validated_at DESC
            LIMIT  100
        """), {"task_id": task_id})

        if len(df) < 10:
            return False

        real_prec = float(df["was_correct"].mean())
        baseline  = self._baseline_precision(task_id)
        return (baseline - real_prec) >= DRIFT_THRESHOLD

    def get_full_health_report(self) -> list:
        order = {"CRITICAL": 0, "WARNING": 1, "NO_DATA": 2, "GOOD": 3}
        report = [self.get_model_health(t) for t in self._registry]
        report.sort(key=lambda x: order.get(x["health_status"], 9))
        return report

    def update_registry_health(self, health_report: list):
        for h in health_report:
            tid = h["task_id"]
            if tid not in self._registry:
                continue
            self._registry[tid].update({
                "real_precision":   h["real_precision"],
                "health_status":    h["health_status"],
                "drift_detected":   h["drift"] is not None and h["drift"] >= DRIFT_THRESHOLD,
                "last_validated":   datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            })

        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(self._registry, f, indent=2, ensure_ascii=False)
        log.info("Registry updated with health data for %d tasks", len(health_report))


# =============================================================================
# COMPONENT 4 — Retraining Trigger
# =============================================================================

class RetrainingTrigger:
    def __init__(self, monitor: ModelHealthMonitor,
                 drift_threshold: float = DRIFT_THRESHOLD):
        self.monitor         = monitor
        self.drift_threshold = drift_threshold

    def check_and_trigger(self) -> list:
        report  = self.monitor.get_full_health_report()
        queue   = self._load_queue()
        queued  = []
        existing_tasks = {item["task_id"] for item in queue if item["status"] == "pending"}

        for h in report:
            if h["health_status"] == "CRITICAL" and h["task_id"] not in existing_tasks:
                entry = {
                    "task_id":        h["task_id"],
                    "status":         "pending",
                    "queued_at":      datetime.now(timezone.utc).isoformat(),
                    "real_precision": h["real_precision"],
                    "baseline":       h["baseline_precision"],
                    "drift":          h["drift"],
                    "priority":       "HIGH" if (h["drift"] or 0) > 0.20 else "NORMAL",
                }
                queue.append(entry)
                queued.append(h["task_id"])
                log.warning("Queued %s for retraining (drift=%.3f)", h["task_id"], h["drift"] or 0)

        if queued:
            self._save_queue(queue)

        return queued

    def get_retraining_queue(self) -> list:
        queue = self._load_queue()
        pending = [q for q in queue if q["status"] == "pending"]
        pending.sort(key=lambda x: (0 if x.get("priority") == "HIGH" else 1,
                                    x.get("queued_at", "")))
        return pending

    def mark_done(self, task_id: str):
        queue = self._load_queue()
        for item in queue:
            if item["task_id"] == task_id and item["status"] == "pending":
                item["status"]      = "completed"
                item["completed_at"]= datetime.now(timezone.utc).isoformat()
        self._save_queue(queue)

    def _load_queue(self) -> list:
        if os.path.exists(QUEUE_PATH):
            with open(QUEUE_PATH, encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_queue(self, queue: list):
        with open(QUEUE_PATH, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)


# =============================================================================
# COMPONENT 5 — Feedback Dashboard CLI
# =============================================================================

class FeedbackCLI:
    def __init__(self, db: MedinoteDB, registry_path: str = REGISTRY_PATH):
        self.db      = db
        self.monitor = ModelHealthMonitor(db, registry_path)
        self.trigger = RetrainingTrigger(self.monitor)

    def show_health(self):
        report = self.monitor.get_full_health_report()
        STATUS_COLOR = {
            "GOOD":     "\033[32m",   # green
            "WARNING":  "\033[33m",   # yellow
            "CRITICAL": "\033[31m",   # red
            "NO_DATA":  "\033[90m",   # grey
        }
        RESET = "\033[0m"

        print(f"\n{'='*105}")
        print(f"  MEDINOTE MODEL HEALTH REPORT  —  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*105}")
        hdr = (f"{'TASK':<35} {'MODE':<7} {'PREDS':>6} {'VALID':>6} "
               f"{'REAL_PREC':>10} {'BASELINE':>9} {'DRIFT':>7} {'STATUS':<10}")
        print(hdr)
        print("-" * 105)

        for h in report:
            prec_str  = f"{h['real_precision']*100:.1f}%" if h['real_precision'] is not None else "  N/A  "
            drift_str = f"{h['drift']*100:+.1f}%"         if h['drift']         is not None else "   N/A "
            color     = STATUS_COLOR.get(h["health_status"], "")
            print(
                f"{h['task_id']:<35} {h['mode']:<7} "
                f"{h['total_predictions']:>6} {h['validated_count']:>6} "
                f"{prec_str:>10} {h['baseline_precision']*100:>8.1f}% "
                f"{drift_str:>7}  "
                f"{color}{h['health_status']:<10}{RESET}"
            )

        print(f"{'='*105}\n")

    def show_retraining_queue(self):
        queue = self.trigger.get_retraining_queue()
        if not queue:
            print("\nRetraining queue is empty — all models healthy.\n")
            return

        print(f"\n{'='*80}")
        print("  RETRAINING QUEUE")
        print(f"{'='*80}")
        print(f"{'TASK':<35} {'PRIORITY':<9} {'DRIFT':>7}  {'QUEUED'}")
        print("-" * 80)
        for q in queue:
            drift_str = f"{q['drift']*100:+.1f}%" if q.get("drift") is not None else "N/A"
            print(f"{q['task_id']:<35} {q.get('priority','?'):<9} "
                  f"{drift_str:>7}  {q.get('queued_at','')[:19]}")
        print(f"{'='*80}\n")

    def run_validation_now(self):
        print("\nRunning validation …")
        validator = OutcomeValidator(self.db)
        result    = validator.validate_due_predictions()
        print(json.dumps(result, indent=2, default=str))

        queued = self.trigger.check_and_trigger()
        if queued:
            print(f"\nQueued for retraining: {queued}")


# =============================================================================
# SCHEDULER
# =============================================================================

def run_scheduler():
    try:
        import schedule
    except ImportError:
        print("Run: pip install schedule")
        sys.exit(1)

    import time

    db        = MedinoteDB()
    validator = OutcomeValidator(db)
    monitor   = ModelHealthMonitor(db, REGISTRY_PATH)
    trigger   = RetrainingTrigger(monitor)

    def _validate():
        log.info("Scheduled validation starting …")
        result = validator.validate_due_predictions()
        log.info("Validation result: %s", result)

    def _drift_check():
        log.info("Scheduled drift check starting …")
        queued = trigger.check_and_trigger()
        if queued:
            log.warning("Drift detected — queued: %s", queued)

    def _health_update():
        log.info("Updating registry health …")
        monitor.update_registry_health(monitor.get_full_health_report())

    schedule.every().day.at("00:00").do(_validate)
    schedule.every().day.at("01:00").do(_health_update)
    schedule.every().week.do(_drift_check)

    print(f"Feedback loop scheduler running — {datetime.now().isoformat()}")
    print("  00:00 daily  → validate due predictions")
    print("  01:00 daily  → update registry health")
    print("  weekly       → drift check + retraining trigger")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nScheduler stopped.")
    finally:
        db.close()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import argparse
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(description="Medinote Feedback Loop")
    parser.add_argument(
        "--mode",
        choices=["health", "validate", "scheduler", "queue"],
        default="health",
        help="health=show table, validate=run now, scheduler=start daemon, queue=retraining list",
    )
    args = parser.parse_args()

    db = MedinoteDB()

    if args.mode == "health":
        cli = FeedbackCLI(db)
        cli.show_health()

    elif args.mode == "validate":
        cli = FeedbackCLI(db)
        cli.run_validation_now()

    elif args.mode == "scheduler":
        db.close()
        run_scheduler()

    elif args.mode == "queue":
        cli = FeedbackCLI(db)
        cli.show_retraining_queue()

    if args.mode != "scheduler":
        db.close()
