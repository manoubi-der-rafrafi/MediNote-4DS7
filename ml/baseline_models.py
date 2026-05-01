"""
Medinote — Baseline Model Training
Trains RandomForest baselines for 4 priority prediction tasks.
Uses live features from FeatureBuilder (db_layer.py).
Time-based split only — never random.
"""

import sys
import os
import json
import joblib
import warnings
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, classification_report,
    mean_absolute_error, mean_squared_error, r2_score,
)

warnings.filterwarnings("ignore")
import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from db_layer import MedinoteDB, FeatureBuilder

# ── Paths ─────────────────────────────────────────────────────────────────────
MODELS_DIR   = r"c:\Users\omri\Desktop\pii\models"
REGISTRY_PATH = os.path.join(MODELS_DIR, "model_registry.json")
os.makedirs(MODELS_DIR, exist_ok=True)

# ── Registry helpers ──────────────────────────────────────────────────────────
def load_registry():
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH) as f:
            return json.load(f)
    return {}

def save_registry(reg):
    with open(REGISTRY_PATH, "w") as f:
        json.dump(reg, f, indent=2)

registry = load_registry()

# ── Shared utilities ──────────────────────────────────────────────────────────
def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def time_split(df, train_frac=0.70):
    """First 70% train, last 30% test — always index order (no shuffle)."""
    n = len(df)
    cut = int(n * train_frac)
    return df.iloc[:cut].copy(), df.iloc[cut:].copy()

def gate_classification(auc):
    if auc >= 0.75:
        return "PASS — ready for optimization"
    if auc >= 0.60:
        return "WEAK — needs better features"
    return "FAIL — go back to label engineering"

def gate_regression(r2):
    if r2 >= 0.60:
        return "PASS — ready for optimization"
    if r2 >= 0.40:
        return "WEAK — needs better features"
    return "FAIL — go back to label engineering"

def save_model(task_id, model, feature_cols):
    model_path   = os.path.join(MODELS_DIR, f"{task_id}_baseline.pkl")
    feature_path = os.path.join(MODELS_DIR, f"{task_id}_features.json")
    joblib.dump(model, model_path)
    with open(feature_path, "w") as f:
        json.dump(feature_cols, f, indent=2)
    print(f"  Saved model  -> {model_path}")
    print(f"  Saved feats  -> {feature_path}")
    return model_path, feature_path

# ── Connect ───────────────────────────────────────────────────────────────────
print("Connecting to database...")
db = MedinoteDB()
fb = FeatureBuilder(db)
print("Connected.\n")

results = []


# ══════════════════════════════════════════════════════════════════════════════
# MODEL 1 — pharmacy_churn_risk  (binary classification)
# ══════════════════════════════════════════════════════════════════════════════
section("MODEL 1 — pharmacy_churn_risk  [binary classification]")

# STEP 1 — Load features
print("\n[Step 1] Loading features from fb.pharmacy_churn_features()...")
df1 = fb.pharmacy_churn_features()
TARGET1 = "churn_label"
ID_COLS1 = ["cl"]
FEAT1 = [c for c in df1.columns if c not in ID_COLS1 + [TARGET1]]

df1 = df1.dropna(subset=[TARGET1])
print(f"  Shape: {df1.shape}   Nulls per feature:\n{df1[FEAT1].isnull().sum().to_dict()}")
print(f"  Target distribution: {df1[TARGET1].value_counts().to_dict()}")
print(f"  Positive rate: {df1[TARGET1].mean()*100:.1f}%")
print(f"  Features: {FEAT1}")
print(f"  NOTE: days_since_last_order directly defines churn_label (>240d).")
print(f"        Model will be near-perfect; treat AUC with caution in production.")

# STEP 2 — Time-based split (index order, no date column)
print("\n[Step 2] Time-based split (index order)...")
train1, test1 = time_split(df1)
X_train1, y_train1 = train1[FEAT1], train1[TARGET1]
X_test1,  y_test1  = test1[FEAT1],  test1[TARGET1]
print(f"  Train: {len(train1)} rows  |  Test: {len(test1)} rows")

# STEP 3 — Class imbalance check
pos_train1 = y_train1.mean()
pos_test1  = y_test1.mean()
print(f"\n[Step 3] Positive rate — train: {pos_train1*100:.1f}%  test: {pos_test1*100:.1f}%")
use_balanced1 = pos_train1 < 0.15 or pos_train1 > 0.85
print(f"  class_weight='balanced': {use_balanced1}")

# STEP 4 — Train
print("\n[Step 4] Training RandomForestClassifier...")
clf1 = RandomForestClassifier(
    n_estimators=100, class_weight="balanced",
    max_depth=6, random_state=42, n_jobs=-1,
)
clf1.fit(X_train1, y_train1)

# STEP 5 — Evaluate
print("\n[Step 5] Evaluation on test set...")
y_prob1 = clf1.predict_proba(X_test1)[:, 1]
y_pred1 = clf1.predict(X_test1)
auc1  = roc_auc_score(y_test1, y_prob1)
prec1 = precision_score(y_test1, y_pred1, zero_division=0)
rec1  = recall_score(y_test1, y_pred1, zero_division=0)
f11   = f1_score(y_test1, y_pred1, zero_division=0)
print(f"  Precision: {prec1:.3f}  Recall: {rec1:.3f}  F1: {f11:.3f}  AUC: {auc1:.3f}")
print(classification_report(y_test1, y_pred1, zero_division=0))

# STEP 6 — Feature importance
fi1 = pd.Series(clf1.feature_importances_, index=FEAT1).sort_values(ascending=False)
print("[Step 6] Top 10 feature importances:")
print(fi1.head(10).to_string())

# STEP 7 — Save
print("\n[Step 7] Saving model...")
mp1, fp1 = save_model("pharmacy_churn_risk", clf1, FEAT1)

# STEP 8 — Registry
verdict1 = gate_classification(auc1)
registry["pharmacy_churn_risk"] = {
    "status": "baseline",
    "type": "classification",
    "last_trained": datetime.today().strftime("%Y-%m-%d"),
    "baseline_auc": round(auc1, 4),
    "baseline_precision": round(prec1, 4),
    "baseline_recall": round(rec1, 4),
    "baseline_f1": round(f11, 4),
    "model_path": mp1,
    "features_path": fp1,
    "verdict": verdict1,
}
save_registry(registry)
print(f"\n  VERDICT: {verdict1}")

results.append({
    "task_id": "pharmacy_churn_risk",
    "type": "classification",
    "train_size": len(train1),
    "test_size": len(test1),
    "metric_name": "auc",
    "metric_value": round(auc1, 4),
    "verdict": verdict1.split(" — ")[0],
    "top_features": fi1.head(5).index.tolist(),
    "model_saved": mp1,
    "note": "days_since_last_order partially defines label — AUC inflated; acceptable for baseline.",
})


# ══════════════════════════════════════════════════════════════════════════════
# MODEL 2 — delegate_performance_score  (regression)
# ══════════════════════════════════════════════════════════════════════════════
section("MODEL 2 — delegate_performance_score  [regression]")

# STEP 1
print("\n[Step 1] Loading features from fb.delegate_performance_features()...")
df2 = fb.delegate_performance_features()
TARGET2 = "performance_score"
ID_COLS2 = ["dlg"]
FEAT2 = [c for c in df2.columns if c not in ID_COLS2 + [TARGET2]]

df2 = df2.dropna(subset=[TARGET2])
print(f"  Shape: {df2.shape}  (small dataset — ~40 delegates)")
print(f"  Nulls: {df2[FEAT2].isnull().sum().to_dict()}")
print(f"  Target stats: mean={df2[TARGET2].mean():.3f}  std={df2[TARGET2].std():.3f}  "
      f"min={df2[TARGET2].min():.3f}  max={df2[TARGET2].max():.3f}")
print(f"  Features: {FEAT2}")
print(f"  NOTE: Only {len(df2)} delegates — R² will be unstable; interpret cautiously.")

# STEP 2
print("\n[Step 2] Time-based split (index order)...")
train2, test2 = time_split(df2)
X_train2, y_train2 = train2[FEAT2], train2[TARGET2]
X_test2,  y_test2  = test2[FEAT2],  test2[TARGET2]
print(f"  Train: {len(train2)} rows  |  Test: {len(test2)} rows")

# STEP 4 — Regression, no imbalance step
print("\n[Step 4] Training RandomForestRegressor...")
reg2 = RandomForestRegressor(
    n_estimators=100, max_depth=6, random_state=42, n_jobs=-1,
)
reg2.fit(X_train2, y_train2)

# STEP 5
print("\n[Step 5] Evaluation on test set...")
y_pred2 = reg2.predict(X_test2)
mae2  = mean_absolute_error(y_test2, y_pred2)
rmse2 = np.sqrt(mean_squared_error(y_test2, y_pred2))
r2_2  = r2_score(y_test2, y_pred2)
print(f"  MAE: {mae2:.4f}  RMSE: {rmse2:.4f}  R²: {r2_2:.4f}")
sample2 = test2[ID_COLS2].copy()
sample2["actual"]    = y_test2.values
sample2["predicted"] = y_pred2
print("  Actual vs Predicted (5 rows):")
print(sample2.head(5).to_string(index=False))

# STEP 6
fi2 = pd.Series(reg2.feature_importances_, index=FEAT2).sort_values(ascending=False)
print("\n[Step 6] Top feature importances:")
print(fi2.head(10).to_string())

# STEP 7
print("\n[Step 7] Saving model...")
mp2, fp2 = save_model("delegate_performance_score", reg2, FEAT2)

# STEP 8
verdict2 = gate_regression(r2_2)
registry["delegate_performance_score"] = {
    "status": "baseline",
    "type": "regression",
    "last_trained": datetime.today().strftime("%Y-%m-%d"),
    "baseline_mae": round(mae2, 4),
    "baseline_rmse": round(rmse2, 4),
    "baseline_r2": round(r2_2, 4),
    "model_path": mp2,
    "features_path": fp2,
    "verdict": verdict2,
}
save_registry(registry)
print(f"\n  VERDICT: {verdict2}")

results.append({
    "task_id": "delegate_performance_score",
    "type": "regression",
    "train_size": len(train2),
    "test_size": len(test2),
    "metric_name": "r2",
    "metric_value": round(r2_2, 4),
    "verdict": verdict2.split(" — ")[0],
    "top_features": fi2.head(5).index.tolist(),
    "model_saved": mp2,
    "note": f"Only {len(df2)} delegates; R² unreliable at this sample size.",
})


# ══════════════════════════════════════════════════════════════════════════════
# MODEL 3 — sales_forecast_30d  (regression)
# ══════════════════════════════════════════════════════════════════════════════
section("MODEL 3 — sales_forecast_30d  [regression]")

# STEP 1
print("\n[Step 1] Loading features from fb.sales_forecast_features()...")
df3 = fb.sales_forecast_features()
TARGET3 = "target_revenue_30d"
ID_COLS3 = ["cl"]
# Drop revenue_30d — it is identical to the target (leakage)
FEAT3 = [c for c in df3.columns if c not in ID_COLS3 + [TARGET3, "revenue_30d"]]

df3 = df3.dropna(subset=[TARGET3])
print(f"  Shape: {df3.shape}")
print(f"  Nulls: {df3[FEAT3].isnull().sum().to_dict()}")
print(f"  Target stats: mean={df3[TARGET3].mean():.1f}  std={df3[TARGET3].std():.1f}  "
      f"min={df3[TARGET3].min():.1f}  max={df3[TARGET3].max():.1f}")
print(f"  Features: {FEAT3}")
print(f"  NOTE: revenue_30d excluded (= target). Using lagged windows only.")

# STEP 2
print("\n[Step 2] Time-based split (index order)...")
train3, test3 = time_split(df3)
X_train3, y_train3 = train3[FEAT3].fillna(0), train3[TARGET3]
X_test3,  y_test3  = test3[FEAT3].fillna(0),  test3[TARGET3]
print(f"  Train: {len(train3)} rows  |  Test: {len(test3)} rows")

# STEP 4
print("\n[Step 4] Training RandomForestRegressor...")
reg3 = RandomForestRegressor(
    n_estimators=100, max_depth=6, random_state=42, n_jobs=-1,
)
reg3.fit(X_train3, y_train3)

# STEP 5
print("\n[Step 5] Evaluation on test set...")
y_pred3 = reg3.predict(X_test3)
mae3  = mean_absolute_error(y_test3, y_pred3)
rmse3 = np.sqrt(mean_squared_error(y_test3, y_pred3))
r2_3  = r2_score(y_test3, y_pred3)
print(f"  MAE: {mae3:.2f}  RMSE: {rmse3:.2f}  R²: {r2_3:.4f}")
sample3 = test3[ID_COLS3].copy()
sample3["actual"]    = y_test3.values
sample3["predicted"] = y_pred3.round(2)
print("  Actual vs Predicted (5 rows):")
print(sample3.head(5).to_string(index=False))

# STEP 6
fi3 = pd.Series(reg3.feature_importances_, index=FEAT3).sort_values(ascending=False)
print("\n[Step 6] Top feature importances:")
print(fi3.head(10).to_string())

# STEP 7
print("\n[Step 7] Saving model...")
mp3, fp3 = save_model("sales_forecast_30d", reg3, FEAT3)

# STEP 8
verdict3 = gate_regression(r2_3)
registry["sales_forecast_30d"] = {
    "status": "baseline",
    "type": "regression",
    "last_trained": datetime.today().strftime("%Y-%m-%d"),
    "baseline_mae": round(float(mae3), 4),
    "baseline_rmse": round(float(rmse3), 4),
    "baseline_r2": round(float(r2_3), 4),
    "model_path": mp3,
    "features_path": fp3,
    "verdict": verdict3,
}
save_registry(registry)
print(f"\n  VERDICT: {verdict3}")

results.append({
    "task_id": "sales_forecast_30d",
    "type": "regression",
    "train_size": len(train3),
    "test_size": len(test3),
    "metric_name": "r2",
    "metric_value": round(float(r2_3), 4),
    "verdict": verdict3.split(" — ")[0],
    "top_features": fi3.head(5).index.tolist(),
    "model_saved": mp3,
    "note": "revenue_30d excluded (= target). Lagged 60/90/180d windows used only.",
})


# ══════════════════════════════════════════════════════════════════════════════
# MODEL 4 — product_demand_forecast  (regression)
# ══════════════════════════════════════════════════════════════════════════════
section("MODEL 4 — product_demand_forecast  [regression]")

# STEP 1
print("\n[Step 1] Loading features from fb.product_demand_features()...")
df4 = fb.product_demand_features()
TARGET4 = "target_demand_30d"
ID_COLS4 = ["art"]
# Drop revenue_30d — identical to target (leakage)
FEAT4 = [c for c in df4.columns if c not in ID_COLS4 + [TARGET4, "revenue_30d"]]

df4 = df4.dropna(subset=[TARGET4])
print(f"  Shape: {df4.shape}")
print(f"  Nulls: {df4[FEAT4].isnull().sum().to_dict()}")
print(f"  Target stats: mean={df4[TARGET4].mean():.1f}  std={df4[TARGET4].std():.1f}  "
      f"min={df4[TARGET4].min():.1f}  max={df4[TARGET4].max():.1f}")
print(f"  Features: {FEAT4}")
print(f"  NOTE: revenue_30d excluded (= target). Using lagged windows only.")

# STEP 2
print("\n[Step 2] Time-based split (index order)...")
train4, test4 = time_split(df4)
X_train4, y_train4 = train4[FEAT4].fillna(0), train4[TARGET4]
X_test4,  y_test4  = test4[FEAT4].fillna(0),  test4[TARGET4]
print(f"  Train: {len(train4)} rows  |  Test: {len(test4)} rows")

# STEP 4
print("\n[Step 4] Training RandomForestRegressor...")
reg4 = RandomForestRegressor(
    n_estimators=100, max_depth=6, random_state=42, n_jobs=-1,
)
reg4.fit(X_train4, y_train4)

# STEP 5
print("\n[Step 5] Evaluation on test set...")
y_pred4 = reg4.predict(X_test4)
mae4  = mean_absolute_error(y_test4, y_pred4)
rmse4 = np.sqrt(mean_squared_error(y_test4, y_pred4))
r2_4  = r2_score(y_test4, y_pred4)
print(f"  MAE: {mae4:.2f}  RMSE: {rmse4:.2f}  R²: {r2_4:.4f}")
sample4 = test4[ID_COLS4].copy()
sample4["actual"]    = y_test4.values
sample4["predicted"] = y_pred4.round(2)
print("  Actual vs Predicted (5 rows):")
print(sample4.head(5).to_string(index=False))

# STEP 6
fi4 = pd.Series(reg4.feature_importances_, index=FEAT4).sort_values(ascending=False)
print("\n[Step 6] Top feature importances:")
print(fi4.head(10).to_string())

# STEP 7
print("\n[Step 7] Saving model...")
mp4, fp4 = save_model("product_demand_forecast", reg4, FEAT4)

# STEP 8
verdict4 = gate_regression(r2_4)
registry["product_demand_forecast"] = {
    "status": "baseline",
    "type": "regression",
    "last_trained": datetime.today().strftime("%Y-%m-%d"),
    "baseline_mae": round(float(mae4), 4),
    "baseline_rmse": round(float(rmse4), 4),
    "baseline_r2": round(float(r2_4), 4),
    "model_path": mp4,
    "features_path": fp4,
    "verdict": verdict4,
}
save_registry(registry)
print(f"\n  VERDICT: {verdict4}")

results.append({
    "task_id": "product_demand_forecast",
    "type": "regression",
    "train_size": len(train4),
    "test_size": len(test4),
    "metric_name": "r2",
    "metric_value": round(float(r2_4), 4),
    "verdict": verdict4.split(" — ")[0],
    "top_features": fi4.head(5).index.tolist(),
    "model_saved": mp4,
    "note": "revenue_30d excluded (= target). Lagged 60/90d windows + distinct_buyers used.",
})


# ══════════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
db.close()

ready   = [r["task_id"] for r in results if r["verdict"] == "PASS"]
review  = [r["task_id"] for r in results if r["verdict"] != "PASS"]

summary = {
    "baseline_date": datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
    "models_trained": 4,
    "results": results,
    "models_ready_for_optimization": ready,
    "models_needing_review": review,
}

section("FINAL SUMMARY")
print(json.dumps(summary, indent=2))
