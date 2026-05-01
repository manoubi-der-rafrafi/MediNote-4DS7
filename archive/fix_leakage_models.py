"""
Medinote -- Fix Leakage Models
Removes leaking features from 2 models with fake AUC=1.0 and retrains honestly.

FIX 1: campaign_response_probability -- remove order_last_14d (defines label)
FIX 2: cross_sell_ranking -- remove pharmacy_bought_last_90d (inverse of target)
"""

import sys, os, json, warnings
from datetime import datetime

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score,
    f1_score, classification_report,
)

warnings.filterwarnings("ignore")
sys.path.append(r"c:\Users\omri\Desktop\pii")
from db_layer import MedinoteDB, FeatureBuilder

MODELS_DIR    = r"c:\Users\omri\Desktop\pii\models"
LABELS_DIR    = r"c:\Users\omri\Desktop\pii\labels"
REGISTRY_PATH = os.path.join(MODELS_DIR, "model_registry.json")

# ── Helpers ───────────────────────────────────────────────────────────────────
def section(title):
    print("\n" + "=" * 65)
    print("  " + title)
    print("=" * 65)

def time_split(df, frac=0.70):
    cut = int(len(df) * frac)
    return df.iloc[:cut].copy(), df.iloc[cut:].copy()

def gate(auc):
    if auc >= 0.75: return "PASS", "mode1"
    if auc >= 0.60: return "WEAK", "mode2"
    return "FAIL", "mode2"

def load_registry():
    with open(REGISTRY_PATH) as f:
        return json.load(f)

def save_registry(reg):
    with open(REGISTRY_PATH, "w") as f:
        json.dump(reg, f, indent=2, default=str)

def count_modes(reg):
    m1 = sum(1 for v in reg.values() if v.get("mode_active") == "mode1")
    m2 = sum(1 for v in reg.values() if v.get("mode_active") == "mode2")
    return m1, m2

def train_and_evaluate(X_tr, y_tr, X_te, y_te, feat_cols):
    """Train RF with balanced weights, return model + metrics."""
    clf = RandomForestClassifier(
        n_estimators=100, max_depth=6,
        class_weight="balanced", random_state=42, n_jobs=-1,
    )
    clf.fit(X_tr, y_tr)

    # Guard: single-class in test
    if len(y_te.unique()) < 2:
        print("  WARNING: Only one class in test set -- AUC set to 0.5")
        auc = 0.5
    else:
        auc = roc_auc_score(y_te, clf.predict_proba(X_te)[:, 1])

    y_pred = clf.predict(X_te)
    prec   = precision_score(y_te, y_pred, zero_division=0)
    rec    = recall_score(y_te, y_pred, zero_division=0)
    f1     = f1_score(y_te, y_pred, zero_division=0)
    fi     = pd.Series(clf.feature_importances_, index=feat_cols).sort_values(ascending=False)
    return clf, auc, prec, rec, f1, fi

registry = load_registry()
results  = []

# ── Preload DB features (both fixes need churn + product demand) ──────────────
section("PRELOADING DB FEATURES")
print("\n[1/2] pharmacy_churn_features()  (may take 2-3 min)...")
db = MedinoteDB()
fb = FeatureBuilder(db)
df_churn = fb.pharmacy_churn_features()
print(f"      -> {df_churn.shape}  cols: {list(df_churn.columns)}")

print("[2/2] product_demand_features()...")
df_prod = fb.product_demand_features()
print(f"      -> {df_prod.shape}  cols: {list(df_prod.columns)}")
db.close()
print("DB features loaded.\n")


# =============================================================================
# FIX 1 -- campaign_response_probability
# Remove: order_last_14d  (directly defines label)
# =============================================================================
section("FIX 1 -- campaign_response_probability  [remove order_last_14d]")

# Step 1: Load label file
print("\n[Step 1] Loading label file...")
df_cr = pd.read_csv(os.path.join(LABELS_DIR, "campaign_response_labels.csv"))
print(f"  Label shape: {df_cr.shape}  cols: {list(df_cr.columns)}")
print(f"  Target distribution: {df_cr['campaign_response'].value_counts().to_dict()}")
print(f"  Positive rate (full): {df_cr['campaign_response'].mean()*100:.1f}%")

# Step 2: Build honest features -- merge churn, drop leaking column
print("\n[Step 2] Building honest features (NO order_last_14d)...")
churn_cols = ["cl", "days_since_last_order", "order_count_30d", "order_count_90d",
              "revenue_30d", "revenue_90d", "revenue_trend", "churn_label"]
df_cr = df_cr.merge(df_churn[churn_cols], on="cl", how="left")

# Confirm leaking feature is excluded
FEAT_CR = ["days_since_last_order", "order_count_30d", "order_count_90d",
           "revenue_30d", "revenue_90d", "revenue_trend", "churn_label"]
assert "order_last_14d" not in FEAT_CR, "LEAKAGE: order_last_14d still in features!"
print(f"  Final features: {FEAT_CR}")
print(f"  Leaking feature 'order_last_14d': EXCLUDED -- confirmed")

df_cr = df_cr.dropna(subset=["campaign_response"]).copy()
df_cr[FEAT_CR] = df_cr[FEAT_CR].fillna(0)

# Step 3: Class balance
pos_rate_cr = df_cr["campaign_response"].mean()
print(f"\n[Step 3] Positive rate: {pos_rate_cr*100:.1f}%  -> class_weight='balanced' applied")

# Step 4: Time-based split (sort by cl as proxy)
print("\n[Step 4] Time-based split (sorted by cl)...")
df_cr = df_cr.sort_values("cl").reset_index(drop=True)
train_cr, test_cr = time_split(df_cr)
X_tr_cr = train_cr[FEAT_CR]
X_te_cr  = test_cr[FEAT_CR]
y_tr_cr  = train_cr["campaign_response"]
y_te_cr  = test_cr["campaign_response"]
print(f"  Train: {len(train_cr)} | Test: {len(test_cr)}")
print(f"  Positive rate -- train: {y_tr_cr.mean()*100:.1f}%  test: {y_te_cr.mean()*100:.1f}%")

# Step 5-6: Train and evaluate
print("\n[Step 5] Training RandomForestClassifier...")
clf_cr, auc_cr, prec_cr, rec_cr, f1_cr, fi_cr = train_and_evaluate(
    X_tr_cr, y_tr_cr, X_te_cr, y_te_cr, FEAT_CR
)
print(f"\n[Step 6] Evaluation:")
print(f"  Honest AUC : {auc_cr:.4f}  (previous fake AUC: 1.0000)")
print(f"  Precision  : {prec_cr:.3f}  Recall: {rec_cr:.3f}  F1: {f1_cr:.3f}")
print(f"\n  Top 5 features by importance:")
print(fi_cr.head(5).to_string())
print(f"\n  Classification report:")
print(classification_report(y_te_cr, clf_cr.predict(X_te_cr), zero_division=0))

# Step 7: Verdict
verdict_cr, mode_cr = gate(auc_cr)
print(f"[Step 7] VERDICT: {verdict_cr} | MODE: {mode_cr}")

# Step 8: Save
mp_cr = os.path.join(MODELS_DIR, "campaign_response_fixed.pkl")
fp_cr = os.path.join(MODELS_DIR, "campaign_response_features.json")
joblib.dump(clf_cr, mp_cr)
with open(fp_cr, "w") as f:
    json.dump(FEAT_CR, f, indent=2)
print(f"\n[Step 8] Saved -> {mp_cr}")

# Update registry
registry["campaign_response_probability"].update({
    "status": "live" if mode_cr == "mode1" else "weak",
    "model_path": mp_cr,
    "features_path": fp_cr,
    "last_trained": datetime.today().strftime("%Y-%m-%d"),
    "leakage_fixed": True,
    "previous_auc": 1.0,
    "honest_auc": round(auc_cr, 4),
    "production_ready": mode_cr == "mode1",
    "mode_active": mode_cr,
    "notes": "leakage removed -- order_last_14d excluded, retrained on behavioral features only",
})
save_registry(registry)

results.append({
    "task_id": "campaign_response_probability",
    "previous_auc": 1.0,
    "honest_auc": round(auc_cr, 4),
    "leakage_feature_removed": "order_last_14d",
    "verdict": verdict_cr,
    "mode_active": mode_cr,
})


# =============================================================================
# FIX 2 -- cross_sell_ranking
# Remove: pharmacy_bought_last_90d  (inverse of target)
# =============================================================================
section("FIX 2 -- cross_sell_ranking  [remove pharmacy_bought_last_90d]")

# Step 1: Load label file
print("\n[Step 1] Loading label file...")
df_cs = pd.read_csv(os.path.join(LABELS_DIR, "cross_sell_ranking_labels.csv"))
print(f"  Label shape: {df_cs.shape}  cols: {list(df_cs.columns)}")
print(f"  Target distribution: {df_cs['cross_sell_opportunity'].value_counts().to_dict()}")

# Step 2: Build honest features -- drop leaking column, merge external features
print("\n[Step 2] Building honest features (NO pharmacy_bought_last_90d)...")

# Merge pharmacy churn features on cl (rename to avoid collision with product features)
churn_cs = df_churn[["cl", "days_since_last_order", "revenue_90d",
                       "order_count_90d", "churn_label"]].copy()
churn_cs = churn_cs.rename(columns={
    "revenue_90d":     "pharmacy_revenue_90d",
    "order_count_90d": "pharmacy_order_count_90d",
})
df_cs = df_cs.merge(churn_cs, on="cl", how="left")

# Merge product demand features on art (rename to avoid collision)
# Note: product_demand_features has no order_count_90d -- using available cols only
prod_cs = df_prod[["art", "revenue_90d", "distinct_buyers_90d"]].copy()
prod_cs = prod_cs.rename(columns={"revenue_90d": "product_revenue_90d"})
df_cs = df_cs.merge(prod_cs, on="art", how="left")

FEAT_CS = ["product_popularity_pct",
           "days_since_last_order", "pharmacy_revenue_90d",
           "pharmacy_order_count_90d", "churn_label",
           "product_revenue_90d", "distinct_buyers_90d"]

# Confirm leaking feature is excluded
assert "pharmacy_bought_last_90d" not in FEAT_CS, "LEAKAGE: pharmacy_bought_last_90d still in features!"
print(f"  Final features: {FEAT_CS}")
print(f"  Leaking feature 'pharmacy_bought_last_90d': EXCLUDED -- confirmed")
print(f"  Note: product_order_count_90d not available in product_demand_features -- skipped")

# Step 3: Sample if > 50,000 rows
print(f"\n[Step 3] Row count before sampling: {len(df_cs)}")
if len(df_cs) > 50000:
    df_cs = df_cs.sample(50000, random_state=42).reset_index(drop=True)
    print(f"  Sampled to: {len(df_cs)} rows")
else:
    print(f"  No sampling needed ({len(df_cs)} rows < 50,000)")

df_cs = df_cs.dropna(subset=["cross_sell_opportunity"]).copy()
df_cs[FEAT_CS] = df_cs[FEAT_CS].fillna(0)

# Step 4: Class balance
pos_rate_cs = df_cs["cross_sell_opportunity"].mean()
print(f"\n[Step 4] Positive rate: {pos_rate_cs*100:.1f}%  -> class_weight='balanced' applied")

# Step 5: Time-based split (sort by product_popularity_pct descending)
print("\n[Step 5] Time-based split (sorted by product_popularity_pct desc)...")
df_cs = df_cs.sort_values("product_popularity_pct", ascending=False).reset_index(drop=True)
train_cs, test_cs = time_split(df_cs)
X_tr_cs = train_cs[FEAT_CS]
X_te_cs  = test_cs[FEAT_CS]
y_tr_cs  = train_cs["cross_sell_opportunity"]
y_te_cs  = test_cs["cross_sell_opportunity"]
print(f"  Train: {len(train_cs)} | Test: {len(test_cs)}")
print(f"  Positive rate -- train: {y_tr_cs.mean()*100:.1f}%  test: {y_te_cs.mean()*100:.1f}%")

# Step 6-7: Train and evaluate
print("\n[Step 6] Training RandomForestClassifier...")
clf_cs, auc_cs, prec_cs, rec_cs, f1_cs, fi_cs = train_and_evaluate(
    X_tr_cs, y_tr_cs, X_te_cs, y_te_cs, FEAT_CS
)
print(f"\n[Step 7] Evaluation:")
print(f"  Honest AUC : {auc_cs:.4f}  (previous fake AUC: 1.0000)")
print(f"  Precision  : {prec_cs:.3f}  Recall: {rec_cs:.3f}  F1: {f1_cs:.3f}")
print(f"\n  Top 5 features by importance:")
print(fi_cs.head(5).to_string())
print(f"\n  Classification report:")
print(classification_report(y_te_cs, clf_cs.predict(X_te_cs), zero_division=0))

# Step 8: Verdict
verdict_cs, mode_cs = gate(auc_cs)
print(f"[Step 8] VERDICT: {verdict_cs} | MODE: {mode_cs}")

# Step 9: Save
mp_cs = os.path.join(MODELS_DIR, "cross_sell_ranking_fixed.pkl")
fp_cs = os.path.join(MODELS_DIR, "cross_sell_ranking_features.json")
joblib.dump(clf_cs, mp_cs)
with open(fp_cs, "w") as f:
    json.dump(FEAT_CS, f, indent=2)
print(f"\n[Step 9] Saved -> {mp_cs}")

# Update registry
registry["cross_sell_ranking"].update({
    "status": "live" if mode_cs == "mode1" else "weak",
    "model_path": mp_cs,
    "features_path": fp_cs,
    "last_trained": datetime.today().strftime("%Y-%m-%d"),
    "leakage_fixed": True,
    "previous_auc": 1.0,
    "honest_auc": round(auc_cs, 4),
    "production_ready": mode_cs == "mode1",
    "mode_active": mode_cs,
    "notes": "leakage removed -- pharmacy_bought_last_90d excluded, retrained on popularity + behavior",
})
save_registry(registry)

results.append({
    "task_id": "cross_sell_ranking",
    "previous_auc": 1.0,
    "honest_auc": round(auc_cs, 4),
    "leakage_feature_removed": "pharmacy_bought_last_90d",
    "verdict": verdict_cs,
    "mode_active": mode_cs,
})


# =============================================================================
# FINAL SUMMARY
# =============================================================================
section("FINAL SUMMARY")

m1_total, m2_total = count_modes(registry)

summary = {
    "fix_date": datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
    "models_fixed": 2,
    "results": results,
    "total_mode1_in_system": m1_total,
    "total_mode2_in_system": m2_total,
}
print(json.dumps(summary, indent=2))

summary_path = os.path.join(MODELS_DIR, "leakage_fix_summary.json")
with open(summary_path, "w") as f:
    json.dump(summary, f, indent=2)
print(f"\nSummary saved -> {summary_path}")
