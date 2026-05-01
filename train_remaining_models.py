"""
Medinote -- Train Remaining 11 Models (Models 5-15)
Follows exact same pattern as Models 1-4 baselines.
All DB features preloaded once at startup to avoid repeated slow queries.
"""

import sys, os, json, warnings
from datetime import datetime

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    classification_report, mean_absolute_error, mean_squared_error, r2_score,
)

warnings.filterwarnings("ignore")
sys.path.append(r"c:\Users\omri\Desktop\pii")
from db_layer import MedinoteDB, FeatureBuilder

MODELS_DIR  = r"c:\Users\omri\Desktop\pii\models"
LABELS_DIR  = r"c:\Users\omri\Desktop\pii\labels"
REGISTRY_PATH = os.path.join(MODELS_DIR, "model_registry.json")
os.makedirs(MODELS_DIR, exist_ok=True)

# ── Shared helpers ────────────────────────────────────────────────────────────

def section(title):
    print("\n" + "=" * 65)
    print("  " + title)
    print("=" * 65)

def time_split(df, frac=0.70):
    cut = int(len(df) * frac)
    return df.iloc[:cut].copy(), df.iloc[cut:].copy()

def safe_predict(model, X):
    return np.maximum(0, model.predict(X))

def gate_cls(auc):
    if auc >= 0.75: return "PASS", "mode1"
    if auc >= 0.60: return "WEAK", "mode2"
    return "FAIL", "mode2"

def gate_reg(r2):
    if r2 >= 0.65: return "PASS", "mode1"
    if r2 >= 0.40: return "WEAK", "mode2"
    return "FAIL", "mode2"

def load_registry():
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH) as f:
            return json.load(f)
    return {}

def save_registry(reg):
    with open(REGISTRY_PATH, "w") as f:
        json.dump(reg, f, indent=2, default=str)

results = []

# ── Train / evaluate / save helper ───────────────────────────────────────────
def train_model(task_id, model_type, df, feat_cols, target_col,
                sample_warning=False, registry=None):
    """
    Full pipeline: split -> train -> evaluate -> save -> register.
    Returns result dict.
    """
    df = df.dropna(subset=[target_col]).copy()
    df[feat_cols] = df[feat_cols].fillna(0)

    print(f"\n  Shape after dropna: {df.shape}")
    print(f"  Features ({len(feat_cols)}): {feat_cols}")
    if sample_warning:
        print(f"  WARNING: small sample ({len(df)} rows) -- model directional only")

    # Time-based split
    train, test = time_split(df)
    X_tr, y_tr = train[feat_cols], train[target_col]
    X_te, y_te = test[feat_cols],  test[target_col]
    print(f"  Train: {len(train)}  |  Test: {len(test)}")

    # Train
    if model_type == "classification":
        pos_rate = y_tr.mean()
        print(f"  Positive rate (train): {pos_rate*100:.1f}%")

        # Guard: single-class training set makes AUC undefined
        if len(y_tr.unique()) < 2:
            print("  WARNING: Only one class in training set -- degenerate label.")
            print("  Saving trivial model, marking FAIL.")
            clf = RandomForestClassifier(
                n_estimators=10, max_depth=2, random_state=42, n_jobs=-1,
            )
            clf.fit(X_tr, y_tr)
            auc, prec, rec, f1 = 0.5, 0.0, 0.0, 0.0
            verdict, mode = "FAIL", "mode2"
            metric_name, metric_val = "auc", 0.5
            model_obj = clf
            top3 = feat_cols[:3]
            mp = os.path.join(MODELS_DIR, f"{task_id}_baseline.pkl")
            fp = os.path.join(MODELS_DIR, f"{task_id}_features.json")
            joblib.dump(model_obj, mp)
            with open(fp, "w") as f:
                json.dump(feat_cols, f, indent=2)
            print(f"  Saved -> {mp}")
            print(f"  VERDICT: {verdict} | MODE: {mode}")
            entry = {
                "status": "baseline", "type": model_type,
                "last_trained": datetime.today().strftime("%Y-%m-%d"),
                "model_path": mp, "features_path": fp,
                "metric_name": metric_name, f"baseline_{metric_name}": metric_val,
                "leakage_risk": "none", "sample_size_warning": sample_warning,
                "production_ready": False, "mode_active": mode, "verdict": verdict,
                "notes": "degenerate label -- only one class in training data",
            }
            if registry is not None:
                registry[task_id] = entry
                save_registry(registry)
            return {
                "task_id": task_id, "type": model_type,
                "train_size": len(train), "test_size": len(test),
                "metric_name": metric_name, "metric_value": metric_val,
                "verdict": verdict, "mode_active": mode,
                "sample_warning": sample_warning, "top_3_features": top3,
                "model_saved": mp,
            }

        clf = RandomForestClassifier(
            n_estimators=100, max_depth=6,
            class_weight="balanced", random_state=42, n_jobs=-1,
        )
        clf.fit(X_tr, y_tr)

        # Guard: if test set also single-class, AUC undefined
        if len(y_te.unique()) < 2:
            print("  WARNING: Only one class in test set -- AUC set to 0.5.")
            auc = 0.5
        else:
            proba = clf.predict_proba(X_te)
            auc = roc_auc_score(y_te, proba[:, 1] if proba.shape[1] > 1 else proba[:, 0])

        y_pred = clf.predict(X_te)
        prec  = precision_score(y_te, y_pred, zero_division=0)
        rec   = recall_score(y_te, y_pred, zero_division=0)
        f1    = f1_score(y_te, y_pred, zero_division=0)
        print(f"  AUC: {auc:.4f}  Prec: {prec:.3f}  Rec: {rec:.3f}  F1: {f1:.3f}")
        print(classification_report(y_te, y_pred, zero_division=0))
        verdict, mode = gate_cls(auc)
        metric_name, metric_val = "auc", round(auc, 4)
        model_obj = clf
    else:
        reg = RandomForestRegressor(
            n_estimators=100, max_depth=6, random_state=42, n_jobs=-1,
        )
        reg.fit(X_tr, y_tr)
        y_pred = safe_predict(reg, X_te)
        mae  = mean_absolute_error(y_te, y_pred)
        rmse = np.sqrt(mean_squared_error(y_te, y_pred))
        r2   = r2_score(y_te, y_pred)
        print(f"  MAE: {mae:.2f}  RMSE: {rmse:.2f}  R2: {r2:.4f}")
        verdict, mode = gate_reg(r2)
        metric_name, metric_val = "r2", round(r2, 4)
        model_obj = reg

    # Feature importance
    fi = pd.Series(model_obj.feature_importances_, index=feat_cols).sort_values(ascending=False)
    top3 = fi.head(3).index.tolist()
    print(f"  Top features: {fi.head(6).to_dict()}")

    # Save
    mp = os.path.join(MODELS_DIR, f"{task_id}_baseline.pkl")
    fp = os.path.join(MODELS_DIR, f"{task_id}_features.json")
    joblib.dump(model_obj, mp)
    with open(fp, "w") as f:
        json.dump(feat_cols, f, indent=2)
    print(f"  Saved -> {mp}")
    print(f"  VERDICT: {verdict} | MODE: {mode}")

    # Registry
    entry = {
        "status": "baseline",
        "type": model_type,
        "last_trained": datetime.today().strftime("%Y-%m-%d"),
        "model_path": mp,
        "features_path": fp,
        "metric_name": metric_name,
        f"baseline_{metric_name}": metric_val,
        "leakage_risk": "none",
        "sample_size_warning": sample_warning,
        "production_ready": mode == "mode1",
        "mode_active": mode,
        "verdict": verdict,
        "notes": (
            "small sample -- directional only, retrain when n > 100"
            if sample_warning else ""
        ),
    }
    if registry is not None:
        registry[task_id] = entry
        save_registry(registry)

    return {
        "task_id": task_id,
        "type": model_type,
        "train_size": len(train),
        "test_size": len(test),
        "metric_name": metric_name,
        "metric_value": metric_val,
        "verdict": verdict,
        "mode_active": mode,
        "sample_warning": sample_warning,
        "top_3_features": top3,
        "model_saved": mp,
    }


# ═════════════════════════════════════════════════════════════════════════════
# PRELOAD ALL DB FEATURES ONCE
# ═════════════════════════════════════════════════════════════════════════════
section("PRELOADING DB FEATURES (all models share these)")

db = MedinoteDB()
fb = FeatureBuilder(db)

print("\n[1/4] pharmacy_churn_features()  (may take 2-3 min)...")
df_churn = fb.pharmacy_churn_features()
print(f"      -> {df_churn.shape}  cols: {list(df_churn.columns)}")

print("[2/4] delegate_performance_features()...")
df_dlg_perf = fb.delegate_performance_features()
print(f"      -> {df_dlg_perf.shape}  cols: {list(df_dlg_perf.columns)}")

print("[3/4] product_demand_features()...")
df_prod = fb.product_demand_features()
print(f"      -> {df_prod.shape}  cols: {list(df_prod.columns)}")

print("[4/4] get_pharmacy_summary(days=180)...")
df_pharm_sum = db.get_pharmacy_summary(days=180)
df_pharm_sum["order_frequency"] = df_pharm_sum["order_count"] / 180.0
print(f"      -> {df_pharm_sum.shape}  cols: {list(df_pharm_sum.columns)}")

db.close()
print("\nAll DB features loaded. Starting model training...\n")

registry = load_registry()


# ═════════════════════════════════════════════════════════════════════════════
# MODEL 5 -- payment_default_risk
# ═════════════════════════════════════════════════════════════════════════════
section("MODEL 5 -- payment_default_risk  [classification]")

df5 = pd.read_csv(os.path.join(LABELS_DIR, "payment_default_risk_labels.csv"))
# Add days_since_last_order, order_frequency from pharmacy summary
db_cols = df_pharm_sum[["cl", "days_since_last_order", "order_frequency"]].copy()
df5 = df5.merge(db_cols, on="cl", how="left")

FEAT5 = ["order_count_last_180d", "order_count_prev_180d", "revenue_last_180d",
         "days_since_last_order", "order_frequency"]
r = train_model("payment_default_risk", "classification", df5, FEAT5,
                "payment_risk", registry=registry)
results.append(r)


# ═════════════════════════════════════════════════════════════════════════════
# MODEL 6 -- campaign_response_probability
# ═════════════════════════════════════════════════════════════════════════════
section("MODEL 6 -- campaign_response_probability  [classification]")

df6 = pd.read_csv(os.path.join(LABELS_DIR, "campaign_response_labels.csv"))
churn_add6 = df_churn[["cl", "revenue_90d", "order_frequency_trend",
                        "days_since_last_order"]].copy()
df6 = df6.merge(churn_add6, on="cl", how="left")

FEAT6 = ["order_last_14d", "order_count_last_90d",
         "revenue_90d", "order_frequency_trend", "days_since_last_order"]
r = train_model("campaign_response_probability", "classification", df6, FEAT6,
                "campaign_response", registry=registry)
results.append(r)


# ═════════════════════════════════════════════════════════════════════════════
# MODEL 7 -- visit_priority_ranking
# ═════════════════════════════════════════════════════════════════════════════
section("MODEL 7 -- visit_priority_ranking  [regression]")

df7 = pd.read_csv(os.path.join(LABELS_DIR, "visit_priority_ranking_labels.csv"))
churn_add7 = df_churn[["cl", "order_count_90d", "revenue_trend", "churn_label"]].copy()
df7 = df7.merge(churn_add7, on="cl", how="left")

FEAT7 = ["days_since_last_sale", "revenue_last_90d",
         "order_count_90d", "revenue_trend", "churn_label"]
r = train_model("visit_priority_ranking", "regression", df7, FEAT7,
                "visit_priority_score", registry=registry)
results.append(r)


# ═════════════════════════════════════════════════════════════════════════════
# MODEL 8 -- delegate_target_achievement
# ═════════════════════════════════════════════════════════════════════════════
section("MODEL 8 -- delegate_target_achievement  [classification]")

df8 = pd.read_csv(os.path.join(LABELS_DIR, "delegate_target_achievement_labels.csv"))
dlg_add8 = df_dlg_perf[["dlg", "performance_score",
                          "distinct_pharmacies_90d", "order_count_90d"]].copy()
df8 = df8.merge(dlg_add8, on="dlg", how="left")

FEAT8 = ["revenue_last_30d", "revenue_prev_30d", "revenue_prev_60d",
         "performance_score", "distinct_pharmacies_90d", "order_count_90d"]
warn8 = len(df8) < 50
r = train_model("delegate_target_achievement", "classification", df8, FEAT8,
                "likely_miss_target", sample_warning=warn8, registry=registry)
results.append(r)


# ═════════════════════════════════════════════════════════════════════════════
# MODEL 9 -- order_cancellation_risk
# ═════════════════════════════════════════════════════════════════════════════
section("MODEL 9 -- order_cancellation_risk  [classification]")

df9 = pd.read_csv(os.path.join(LABELS_DIR, "order_cancellation_risk_labels.csv"))
churn_add9 = df_churn[["cl", "revenue_90d", "days_since_last_order",
                        "revenue_trend"]].copy()
df9 = df9.merge(churn_add9, on="cl", how="left")

FEAT9 = ["order_count_last_30d", "order_count_prev_30d",
         "revenue_90d", "days_since_last_order", "revenue_trend"]
r = train_model("order_cancellation_risk", "classification", df9, FEAT9,
                "cancellation_risk", registry=registry)
results.append(r)


# ═════════════════════════════════════════════════════════════════════════════
# MODEL 10 -- complaint_recurrence_risk
# ═════════════════════════════════════════════════════════════════════════════
section("MODEL 10 -- complaint_recurrence_risk  [classification]")

df10 = pd.read_csv(os.path.join(LABELS_DIR, "complaint_recurrence_risk_labels.csv"))
churn_add10 = df_churn[["cl", "revenue_90d", "order_count_90d", "churn_label"]].copy()
df10 = df10.merge(churn_add10, on="cl", how="left")

FEAT10 = ["order_count_last_180d", "max_gap_between_orders",
          "revenue_90d", "order_count_90d", "churn_label"]
r = train_model("complaint_recurrence_risk", "classification", df10, FEAT10,
                "complaint_proxy_risk", registry=registry)
results.append(r)


# ═════════════════════════════════════════════════════════════════════════════
# MODEL 11 -- pharmacy_tier_upgrade
# ═════════════════════════════════════════════════════════════════════════════
section("MODEL 11 -- pharmacy_tier_upgrade  [classification]")

df11 = pd.read_csv(os.path.join(LABELS_DIR, "pharmacy_tier_upgrade_labels.csv"))
churn_add11 = df_churn[["cl", "days_since_last_order",
                          "revenue_trend", "churn_label"]].copy()
df11 = df11.merge(churn_add11, on="cl", how="left")

FEAT11 = ["revenue_last_90d", "revenue_prev_90d",
          "order_count_last_90d", "order_count_prev_90d",
          "days_since_last_order", "revenue_trend", "churn_label"]
r = train_model("pharmacy_tier_upgrade", "classification", df11, FEAT11,
                "tier_upgrade_candidate", registry=registry)
results.append(r)


# ═════════════════════════════════════════════════════════════════════════════
# MODEL 12 -- product_sales_trend
# ═════════════════════════════════════════════════════════════════════════════
section("MODEL 12 -- product_sales_trend  [classification]")

df12 = pd.read_csv(os.path.join(LABELS_DIR, "product_sales_trend_labels.csv"))
# product_demand has revenue_30d/60d/90d -- only add revenue_90d, distinct_buyers_90d
# (order_count_90d not available in product_demand_features; skip gracefully)
prod_add12 = df_prod[["art", "revenue_90d", "distinct_buyers_90d"]].copy()
df12 = df12.merge(prod_add12, on="art", how="left")

FEAT12 = ["revenue_last_30d", "revenue_prev_30d", "revenue_prev_60d",
          "revenue_90d", "distinct_buyers_90d"]
r = train_model("product_sales_trend", "classification", df12, FEAT12,
                "downtrend", registry=registry)
results.append(r)


# ═════════════════════════════════════════════════════════════════════════════
# MODEL 13 -- delegate_activity_drop
# ═════════════════════════════════════════════════════════════════════════════
section("MODEL 13 -- delegate_activity_drop  [classification]")

df13 = pd.read_csv(os.path.join(LABELS_DIR, "delegate_activity_drop_labels.csv"))
dlg_add13 = df_dlg_perf[["dlg", "revenue_90d",
                           "distinct_pharmacies_90d", "performance_score"]].copy()
df13 = df13.merge(dlg_add13, on="dlg", how="left")

FEAT13 = ["order_count_last_30d", "order_count_prev_30d",
          "revenue_90d", "distinct_pharmacies_90d", "performance_score"]
warn13 = len(df13) < 50
r = train_model("delegate_activity_drop", "classification", df13, FEAT13,
                "activity_drop", sample_warning=warn13, registry=registry)
results.append(r)


# ═════════════════════════════════════════════════════════════════════════════
# MODEL 14 -- pharmacy_next_purchase_date
# ═════════════════════════════════════════════════════════════════════════════
section("MODEL 14 -- pharmacy_next_purchase_date  [regression]")

df14 = pd.read_csv(os.path.join(LABELS_DIR, "pharmacy_next_purchase_date_labels.csv"))
churn_add14 = df_churn[["cl", "revenue_90d", "order_count_90d", "revenue_trend"]].copy()
df14 = df14.merge(churn_add14, on="cl", how="left")
# Drop non-feature columns: cl, last_sale_date
df14 = df14.drop(columns=["cl", "last_sale_date"], errors="ignore")

FEAT14 = ["order_count", "days_since_last_sale",
          "revenue_90d", "order_count_90d", "revenue_trend"]
r = train_model("pharmacy_next_purchase_date", "regression", df14, FEAT14,
                "median_days_between_orders", registry=registry)
results.append(r)


# ═════════════════════════════════════════════════════════════════════════════
# MODEL 15 -- cross_sell_ranking
# ═════════════════════════════════════════════════════════════════════════════
section("MODEL 15 -- cross_sell_ranking  [classification]")

df15 = pd.read_csv(os.path.join(LABELS_DIR, "cross_sell_ranking_labels.csv"))
print(f"\n  Label rows: {len(df15)}")

# Sample if > 50,000 rows
if len(df15) > 50000:
    df15 = df15.sample(50000, random_state=42)
    print(f"  Sampled to 50,000 rows")

# Merge pharmacy churn features on cl
churn_add15 = df_churn[["cl", "revenue_90d", "churn_label"]].copy()
churn_add15 = churn_add15.rename(columns={"revenue_90d": "pharm_revenue_90d"})
df15 = df15.merge(churn_add15, on="cl", how="left")

# Merge product demand features on art
prod_add15 = df_prod[["art", "revenue_90d", "distinct_buyers_90d"]].copy()
prod_add15 = prod_add15.rename(columns={"revenue_90d": "product_revenue_90d"})
df15 = df15.merge(prod_add15, on="art", how="left")

# Drop ID columns before training
df15 = df15.drop(columns=["cl", "art"], errors="ignore")

FEAT15 = ["pharmacy_bought_last_90d", "product_popularity_pct",
          "pharm_revenue_90d", "churn_label",
          "product_revenue_90d", "distinct_buyers_90d"]
r = train_model("cross_sell_ranking", "classification", df15, FEAT15,
                "cross_sell_opportunity", registry=registry)
results.append(r)


# ═════════════════════════════════════════════════════════════════════════════
# FINAL COMPARISON TABLE
# ═════════════════════════════════════════════════════════════════════════════
section("FINAL COMPARISON TABLE -- All 11 Models")

header = f"  {'Model':<35} {'Type':<14} {'Train':>6} {'Test':>5} {'Metric':<6} {'Score':>7} {'Verdict':<6} {'Mode'}"
print(header)
print("  " + "-" * 100)
for r in results:
    print(
        f"  {r['task_id']:<35} {r['type']:<14} {r['train_size']:>6} "
        f"{r['test_size']:>5} {r['metric_name']:<6} {r['metric_value']:>7.4f} "
        f"{r['verdict']:<6} {r['mode_active']}"
        + (" [!]" if r["sample_warning"] else "")
    )

mode1 = [r["task_id"] for r in results if r["mode_active"] == "mode1"]
mode2 = [r["task_id"] for r in results if r["mode_active"] == "mode2"]


# ═════════════════════════════════════════════════════════════════════════════
# FINAL JSON SUMMARY
# ═════════════════════════════════════════════════════════════════════════════
section("FINAL JSON SUMMARY")

summary = {
    "training_date": datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
    "models_trained": 11,
    "results": results,
    "total_mode1": len(mode1),
    "total_mode2": len(mode2),
    "total_models_in_system": 15,
    "models_promoted_to_mode1": mode1,
    "models_remaining_mode2": mode2,
}
print(json.dumps(summary, indent=2))

# Save summary
summary_path = os.path.join(MODELS_DIR, "remaining_models_summary.json")
with open(summary_path, "w") as f:
    json.dump(summary, f, indent=2)
print(f"\nSummary saved -> {summary_path}")
