import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

REFERENCE_DATE = pd.Timestamp("2026-01-22")
OUTPUT_DIR = r"c:\Users\omri\Desktop\pii\labels"
DATA_DIR = r"c:\Users\omri\Desktop\pii"

results = []

# ── TASK 1: delegate_performance_score ────────────────────────────────────────
print(">>> TASK 1: delegate_performance_score")

df_dlg = pd.read_csv(os.path.join(DATA_DIR, "sales_with_delegate.csv"),
                     usecols=["dlg", "cl", "date", "ttc"],
                     parse_dates=["date"], dayfirst=False)

cutoff_90 = REFERENCE_DATE - pd.Timedelta(days=90)
w = df_dlg[df_dlg["date"] >= cutoff_90].copy()

agg = w.groupby("dlg").agg(
    revenue_last_90d=("ttc", "sum"),
    order_count_last_90d=("date", "nunique"),
    distinct_pharmacies_last_90d=("cl", "nunique"),
).reset_index()

def minmax(col):
    mn, mx = col.min(), col.max()
    return (col - mn) / (mx - mn) if mx != mn else pd.Series(0.5, index=col.index)

agg["performance_score"] = (
    0.5 * minmax(agg["revenue_last_90d"]) +
    0.3 * minmax(agg["order_count_last_90d"]) +
    0.2 * minmax(agg["distinct_pharmacies_last_90d"])
)

out1 = agg[["dlg", "revenue_last_90d", "order_count_last_90d",
             "distinct_pharmacies_last_90d", "performance_score"]]
out1.to_csv(os.path.join(OUTPUT_DIR, "delegate_performance_score_labels.csv"), index=False)

print(f"    Saved {len(out1)} rows -> delegate_performance_score_labels.csv")
print(f"    Score range: {agg['performance_score'].min():.3f} - {agg['performance_score'].max():.3f}")

results.append({
    "task_id": "delegate_performance_score",
    "type": "regression",
    "record_count": len(out1),
    "positive_rate_pct": None,
    "file_saved": "delegate_performance_score_labels.csv",
    "note": f"score range [{agg['performance_score'].min():.3f}, {agg['performance_score'].max():.3f}]"
})

# ── TASK 2: campaign_response_probability ─────────────────────────────────────
print("\n>>> TASK 2: campaign_response_probability")

df = pd.read_csv(os.path.join(DATA_DIR, "sales_clean.csv"),
                 usecols=["cl", "date", "ttc"],
                 parse_dates=["date"], dayfirst=False)

cutoff_14 = REFERENCE_DATE - pd.Timedelta(days=14)
cutoff_90 = REFERENCE_DATE - pd.Timedelta(days=90)

last14 = df[df["date"] >= cutoff_14].groupby("cl")["date"].count().rename("orders_in_14d")
last90 = df[df["date"] >= cutoff_90].groupby("cl")["date"].count().rename("order_count_last_90d")

all_cl = df["cl"].unique()
base = pd.DataFrame({"cl": all_cl})
base = base.merge(last14, on="cl", how="left").merge(last90, on="cl", how="left").fillna(0)

base["order_last_14d"] = (base["orders_in_14d"] >= 1).astype(int)
base["order_count_last_90d"] = base["order_count_last_90d"].astype(int)
base["campaign_response"] = (
    (base["order_last_14d"] == 1) & (base["order_count_last_90d"] >= 2)
).astype(int)

out2 = base[["cl", "order_last_14d", "order_count_last_90d", "campaign_response"]]
out2.to_csv(os.path.join(OUTPUT_DIR, "campaign_response_labels.csv"), index=False)

pos_rate = base["campaign_response"].mean() * 100
balance_ok = 15.0 <= pos_rate <= 40.0
print(f"    Saved {len(out2)} rows -> campaign_response_labels.csv")
print(f"    Positive rate: {pos_rate:.1f}%  |  Balance OK: {balance_ok}")

results.append({
    "task_id": "campaign_response_probability",
    "type": "classification",
    "record_count": len(out2),
    "positive_rate_pct": round(pos_rate, 2),
    "class_balance_ok": balance_ok,
    "file_saved": "campaign_response_labels.csv",
    "note": f"positive rate {pos_rate:.1f}%"
})

# ── TASK 3: cross_sell_ranking ────────────────────────────────────────────────
print("\n>>> TASK 3: cross_sell_ranking")

df2 = pd.read_csv(os.path.join(DATA_DIR, "sales_clean.csv"),
                  usecols=["cl", "art", "date"],
                  parse_dates=["date"], dayfirst=False)

w90 = df2[df2["date"] >= cutoff_90].copy()

total_pharmacies = w90["cl"].nunique()

# Step 1: product popularity
product_buyers = w90.groupby("art")["cl"].nunique().reset_index()
product_buyers.columns = ["art", "buyer_count"]
product_buyers["product_popularity_pct"] = product_buyers["buyer_count"] / total_pharmacies

popular = product_buyers[product_buyers["product_popularity_pct"] >= 0.20]["art"].values
print(f"    Popular products (>=20% pharmacies): {len(popular)}")

# Step 2: what each pharmacy bought in last 90d (popular products only)
bought = w90[w90["art"].isin(popular)][["cl", "art"]].drop_duplicates()
bought["pharmacy_bought_last_90d"] = 1

# Step 3: all combinations of pharmacies x popular products
all_cl = w90["cl"].unique()
idx = pd.MultiIndex.from_product([all_cl, popular], names=["cl", "art"])
pairs = pd.DataFrame(index=idx).reset_index()

pairs = pairs.merge(bought, on=["cl", "art"], how="left")
pairs["pharmacy_bought_last_90d"] = pairs["pharmacy_bought_last_90d"].fillna(0).astype(int)
pairs = pairs.merge(product_buyers[["art", "product_popularity_pct"]], on="art", how="left")
pairs["cross_sell_opportunity"] = (pairs["pharmacy_bought_last_90d"] == 0).astype(int)

out3 = pairs[["cl", "art", "pharmacy_bought_last_90d",
              "product_popularity_pct", "cross_sell_opportunity"]]
out3.to_csv(os.path.join(OUTPUT_DIR, "cross_sell_ranking_labels.csv"), index=False)

opp_rate = pairs["cross_sell_opportunity"].mean() * 100
print(f"    Saved {len(out3)} rows -> cross_sell_ranking_labels.csv")
print(f"    Opportunity rate: {opp_rate:.1f}%")

results.append({
    "task_id": "cross_sell_ranking",
    "type": "ranking",
    "record_count": len(out3),
    "positive_rate_pct": round(opp_rate, 2),
    "file_saved": "cross_sell_ranking_labels.csv",
    "note": f"{len(popular)} popular products x {len(all_cl)} pharmacies"
})

# ── SUMMARY JSON ──────────────────────────────────────────────────────────────
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        return super().default(obj)

summary = {
    "completion_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "tasks_completed": 3,
    "results": results,
    "all_15_tasks_complete": True
}

print("\n" + json.dumps(summary, indent=2, cls=NumpyEncoder))
