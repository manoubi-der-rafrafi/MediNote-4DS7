# Medinote — AI-Powered Pharma CRM

> End-to-end pharmaceutical CRM intelligence platform: 15 production ML models, a multi-agent orchestrator, four role-specific web dashboards, and a React Native mobile app — all served from a single FastAPI backend.

---

## Table of Contents

1. [What this project does](#1-what-this-project-does)
2. [System Architecture](#2-system-architecture)
3. [ML Pipeline — 15 Models](#3-ml-pipeline--15-models)
   - [Step 1 — Baseline Training (RandomForest)](#step-1--baseline-training-randomforest)
   - [Step 2 — Optimization (XGBoost + GridSearch)](#step-2--optimization-xgboost--gridsearch)
   - [Step 3 — Leakage Detection & Fixes](#step-3--leakage-detection--fixes)
   - [Step 4 — Model Comparison Table](#step-4--model-comparison-table)
   - [Step 5 — Algorithm Choice Rationale](#step-5--algorithm-choice-rationale)
4. [Multi-Agent Orchestrator](#4-multi-agent-orchestrator)
5. [Backend API](#5-backend-api)
6. [Web Dashboards (4 apps)](#6-web-dashboards-4-apps)
7. [Mobile App (React Native)](#7-mobile-app-react-native)
8. [AI Chat Assistant](#8-ai-chat-assistant)
9. [MLOps — Feedback Loop](#9-mlops--feedback-loop)
10. [Setup & Run](#10-setup--run)

---

## 1. What this project does

Medinote transforms raw pharmaceutical sales data (pharmacies, delegates, doctors, products) into actionable intelligence:

| User Role | Key Intelligence |
|-----------|-----------------|
| **Founder / Direction** | Company-wide CA, delegate rankings, geographic heatmaps, anomaly alerts |
| **Supervisor** | Team performance, coaching queue, visit quality scoring |
| **Marketing** | Campaign ROI, RFM segmentation, sentiment analysis, animation management |
| **Delegate** | Daily visit plan (NBA), CA achievement, churn risk per pharmacy, cross-sell recommendations |
| **Pharmacist** | Stock alerts, product demand forecast, tier upgrade opportunity |
| **Doctor** | Prescription history, representative visit history |

Every number shown in the UI comes from the database via the prediction models — no mock data.

---

## 2. System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                │
│                                                                      │
│  direction_web    manager_web    marketing_web    shell              │
│  (React+Vite)     (React+Vite)   (React+Vite)   (React+Vite)        │
│                                                                      │
│              mobile (React Native + Expo 54)                         │
│         Delegate / Doctor / Pharmacist modes                         │
└──────────────────────┬───────────────────────────────────────────────┘
                       │  HTTP / REST  (X-API-Key auth)
┌──────────────────────▼───────────────────────────────────────────────┐
│                      FASTAPI BACKEND  :8000                          │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │               Multi-Agent Orchestrator                       │    │
│  │  Intent Classifier → Data Agent → Prediction Agent          │    │
│  │                     → Explanation Agent                      │    │
│  └──────────────────────────┬──────────────────────────────────┘    │
│                             │                                        │
│  ┌──────────────────────────▼──────────────────────────────────┐    │
│  │               DeepAnalysis BI Engine                         │    │
│  │  pharmacy_analysis · delegate_analysis · rfm · temporal      │    │
│  │  geographic · product_analysis · nlp · animations            │    │
│  └──────────────────────────┬──────────────────────────────────┘    │
│                             │                                        │
│  ┌──────────────────────────▼──────────────────────────────────┐    │
│  │               ML Model Layer  (15 models)                    │    │
│  │  mode1: direct prediction  |  mode2: analytics fallback      │    │
│  └──────────────────────────┬──────────────────────────────────┘    │
│                             │                                        │
│  ┌──────────────────────────▼──────────────────────────────────┐    │
│  │               Feedback Loop (MLOps)                          │    │
│  │  log → validate outcome → detect drift → retrain trigger     │    │
│  └──────────────────────────┬──────────────────────────────────┘    │
└──────────────────────────────┼───────────────────────────────────────┘
                               │  SQLAlchemy ORM
┌──────────────────────────────▼───────────────────────────────────────┐
│                    MariaDB  :3307  /pharma_db                        │
│  ~117 tables: clients, ventes, visites, animations, formations,      │
│  primes, prescriptions, prospects, articles, fournisseurs, zones...  │
└──────────────────────────────────────────────────────────────────────┘
```

**Key design decisions:**

- **Single backend** serves all roles via `X-API-Key` header — no separate microservices needed at this scale.
- **30-minute result cache** on `/predictions/{id}/all-roles` — first call builds all 7 role views (~60s), subsequent calls are instant.
- **`NavigationIndependentTree`** wrapper in the mobile app isolates each role's `NavigationContainer` from expo-router's own navigator, preventing RNSScreen crashes.

---

## 3. ML Pipeline — 15 Models

### Overview

The pipeline was built in four phases: baseline → optimize → fix leakage → deploy.

```
Phase 1           Phase 2              Phase 3           Phase 4
──────────        ──────────────       ────────────────  ──────────
baseline_         optimize_            fix_leakage_      api.py
models.py    →    models.py       →    models.py    →    (serves
                  train_remaining_                       mode1/2)
                  models.py
```

---

### Step 1 — Baseline Training (RandomForest)

**Why RandomForest as baseline?**

RandomForest was chosen as the universal baseline for all 15 tasks because:
- It handles mixed feature types (numeric + categorical) without normalization
- It is robust to missing values via surrogate splits
- It gives reliable feature importance scores with no tuning
- It rarely overfits badly on first run, making it safe to establish a floor

**Split strategy:** Time-based split (`TimeSeriesSplit`) — no random shuffling. This simulates real deployment where the model is trained on past data and scored on future data. Shuffled splits would inflate AUC by up to 15% due to temporal autocorrelation in pharmacy purchase patterns.

**4 initial tasks (baseline_models.py):**

| Task | Type | Baseline AUC/R² | Features |
|------|------|-----------------|----------|
| pharmacy_churn_risk | Classification | AUC 0.8749 | recency, frequency, monetary, days_inactive |
| delegate_performance_score | Regression | R² 0.7902 | visit_rate, ca_per_visit, client_coverage |
| sales_forecast_30d | Regression | R² 0.7020 | rolling_mean, seasonality, product_trend |
| product_demand_forecast | Regression | R² 0.7884 | historical_sales, seasonality, stock_level |

---

### Step 2 — Optimization (XGBoost + GridSearch)

**Why XGBoost over RandomForest for production?**

| Property | RandomForest | XGBoost | Winner |
|----------|-------------|---------|--------|
| Handles missing data | Via surrogates | Native (`missing=NaN`) | XGBoost |
| Training speed on 100k+ rows | Slow (parallel trees) | Fast (histogram boosting) | XGBoost |
| Sensitivity to outliers | Low | Medium | RandomForest |
| Regularization | None (max_features) | L1 + L2 + subsample | XGBoost |
| Monotone constraints | No | Yes (enforced) | XGBoost |
| Best benchmark performance | Good | SOTA on tabular | XGBoost |
| Calibration for probabilities | Poor | Good with `eval_metric=auc` | XGBoost |

XGBoost's gradient boosting corrects residuals sequentially — it learns from previous errors, which is critical for time-series data where patterns are non-linear and evolving.

**GridSearchCV parameters explored:**

```python
param_grid = {
    'n_estimators':   [200, 500],
    'max_depth':      [3, 4, 6],
    'learning_rate':  [0.01, 0.05, 0.1],
    'subsample':      [0.8, 1.0],
}
# 5-fold TimeSeriesSplit cross-validation
# Scoring: AUC for classification, R² for regression
```

**Best parameters found per model:**

| Model | n_estimators | max_depth | lr | subsample |
|-------|-------------|-----------|-----|-----------|
| pharmacy_churn_risk | 200 | 4 | 0.01 | 0.8 |
| sales_forecast_30d | 500 | 4 | 0.01 | 1.0 |
| product_demand_forecast | 500 | 4 | 0.01 | 0.8 |

Low `learning_rate` (0.01) with more trees consistently outperformed high LR — the model learns slowly but generalizes better on pharmacy purchase data.

**11 additional models (train_remaining_models.py):**

| Task | Type | Baseline AUC | Algorithm |
|------|------|-------------|-----------|
| payment_default_risk | Classification | 0.9982 | XGBoost |
| campaign_response_probability | Classification | 0.9985* | XGBoost |
| visit_priority_ranking | Regression | R² 0.5224 | RandomForest |
| delegate_target_achievement | Classification | 0.5000 | XGBoost |
| order_cancellation_risk | Classification | 0.9978 | XGBoost |
| complaint_recurrence_risk | Classification | 0.5000 | XGBoost |
| pharmacy_tier_upgrade | Classification | 0.9993 | XGBoost |
| product_sales_trend | Classification | 0.9090 | XGBoost |
| delegate_activity_drop | Classification | 0.5090 | XGBoost |
| pharmacy_next_purchase_date | Regression | R² −34.10 | XGBoost |
| cross_sell_ranking | Classification | 0.8408* | XGBoost |

*After leakage fix — see Step 3.

---

### Step 3 — Leakage Detection & Fixes

Two models returned `AUC = 1.0` on the test set — a near-perfect score that signals **data leakage** (the model has access to information that would not be available at prediction time).

**campaign_response_probability:**
- Leaked feature: `order_last_14d` — the count of orders placed in the 14 days *after* a campaign was sent
- This is a direct outcome variable disguised as a feature
- Fix: removed `order_last_14d` from feature set, retrained on behavioral features only (visit frequency, product history, RFM segment)
- Honest AUC after fix: **0.9985** (still excellent — real signal exists)

**cross_sell_ranking:**
- Leaked feature: `pharmacy_bought_last_90d` — a binary flag set to 1 if the pharmacy had already bought the cross-sell product
- This is literally the answer to the prediction question
- Fix: removed `pharmacy_bought_last_90d`, retrained on product popularity, co-purchase patterns, and pharmacy profile
- Honest AUC after fix: **0.8408** (good — the model learned real co-purchase patterns)

**Why this matters:** A model with leakage looks perfect in training but fails silently in production because the leaked feature is never available at inference time. Early detection prevented deploying two broken models.

---

### Step 4 — Model Comparison Table

| # | Task | Type | Algorithm | Metric | Score | Production | Mode |
|---|------|------|-----------|--------|-------|------------|------|
| 1 | pharmacy_churn_risk | Class. | XGBoost | AUC | **0.874** | ⚠️ leakage noted | mode2 |
| 2 | delegate_performance_score | Regr. | XGBoost | R² | **0.790** | ⚠️ small N | mode2 |
| 3 | sales_forecast_30d | Regr. | XGBoost | R² | **0.702** | ✅ | mode2 |
| 4 | product_demand_forecast | Regr. | XGBoost | R² | **0.729** | ✅ | mode1 |
| 5 | payment_default_risk | Class. | XGBoost | AUC | **0.998** | ✅ | mode1 |
| 6 | campaign_response | Class. | XGBoost | AUC | **0.999** | ✅ fixed | mode1 |
| 7 | visit_priority_ranking | Regr. | RF | R² | **0.522** | ⚠️ weak | mode2 |
| 8 | delegate_target_achievement | Class. | XGBoost | AUC | **0.500** | ❌ 1 class | mode2 |
| 9 | order_cancellation_risk | Class. | XGBoost | AUC | **0.998** | ✅ | mode1 |
| 10 | complaint_recurrence | Class. | XGBoost | AUC | **0.500** | ❌ | mode2 |
| 11 | pharmacy_tier_upgrade | Class. | XGBoost | AUC | **0.999** | ✅ | mode1 |
| 12 | product_sales_trend | Class. | XGBoost | AUC | **0.909** | ✅ | mode1 |
| 13 | delegate_activity_drop | Class. | XGBoost | AUC | **0.509** | ❌ | mode2 |
| 14 | pharmacy_next_purchase | Regr. | XGBoost | R² | **−34.1** | ❌ | mode2 |
| 15 | cross_sell_ranking | Class. | XGBoost | AUC | **0.841** | ✅ fixed | mode1 |

**Legend:** mode1 = direct ML prediction · mode2 = analytics fallback (model available but supervised by BI engine)

---

### Step 5 — Algorithm Choice Rationale

**Why not deep learning (LSTM, Transformer)?**

- The dataset has ~49 delegates and ~772 pharmacies — too small for deep learning to outperform tree ensembles
- Tabular data with mixed types (dates, categories, counts) is XGBoost's natural domain
- Deep models need normalization, embedding layers, and hyperparameter sensitivity that is overkill here
- XGBoost training takes ~30 seconds; a Transformer baseline would take hours with no gain

**Why not LightGBM?**

LightGBM was considered (faster histogram binning) but XGBoost was chosen because:
- The feature engineering step (`FeatureBuilder`) produces 80+ features, many with high cardinality — XGBoost's `tree_method='hist'` handles this well
- XGBoost's native `missing=NaN` handling avoids explicit imputation steps
- The team's existing debugging tooling was built around XGBoost's `plot_importance`

**Why not logistic regression for classification?**

- Pharmacy purchase patterns are highly non-linear (seasonality × product × zone interactions)
- Logistic regression requires manual interaction terms — XGBoost discovers them automatically
- Tested on pharmacy_churn: logistic regression AUC = 0.71 vs XGBoost 0.87 (+16 points)

---

## 4. Multi-Agent Orchestrator

`orchestrator.py` implements a 4-agent pipeline that converts a natural language query into a structured prediction response:

```
User query (FR/EN)
      │
      ▼
┌─────────────────┐
│  Intent Agent   │  Classifies into 8 intent types:
│                 │  churn_risk · visit_priority · sales_forecast
│                 │  product_demand · payment_risk · cross_sell
│                 │  performance_analysis · unknown (→ mode3 log)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Data Agent    │  Fetches features from MariaDB via FeatureBuilder
│                 │  Caches per pharmacy/delegate ID (TTL: 30 min)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Prediction Agent│  Loads pkl model → runs safe_predict()
│                 │  safe_predict: clips negatives, handles NaN,
│                 │  falls back to analytics median if model fails
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Explanation Agent│  Generates human-readable insight
│                 │  "Pharmacy X has 78% churn risk — last order
│                 │   was 47 days ago, Q4 spend dropped 32%"
└─────────────────┘
```

**mode3 (unknown intent):** Queries that don't match any classifier pattern are logged to `mode3_requests.jsonl` for future model development — the system learns its own gaps.

---

## 5. Backend API

Run: `uvicorn api:app --host 0.0.0.0 --port 8000 --reload`

### Authentication

Two parallel auth mechanisms:

| Method | Header | Used by |
|--------|--------|---------|
| X-API-Key | `X-API-Key: fdr-key-2026` | Mobile app, web dashboards |
| JWT Bearer | `Authorization: Bearer <token>` | Login flow |

**API Key → Role mapping:**

| Key | Role |
|-----|------|
| `fdr-key-2026` | DIRECTION / Founder |
| `sup-key-2026` | SUPERVISEUR |
| `mgr-key-2026` | COMMERCIAL / Manager |
| `mkt-key-2026` | ANIMATRICE / Marketing |
| `dlg-key-2026` | DELEGUE / Delegate |
| `ph-key-2026` | Pharmacy |

### Key Endpoints

```
GET  /predictions/{visit_id}/all-roles   All 7 role views in one call (cached 30 min)
POST /chat                               AI chatbot — context-aware Q&A from real data
GET  /health                             System status
GET  /status                             Detailed component status
POST /auth/login                         JWT login
GET  /dashboard/kpis                     Role-filtered KPI cards
GET  /analytics/geographic               Zone-level sales heatmap
GET  /analytics/delegates                Delegate rankings + coaching alerts
GET  /analytics/rfm                      RFM segments (Champions / Loyal / At-Risk / Lost)
GET  /analytics/products                 Product demand + trend classification
POST /predict                            Free-text ML query (via orchestrator)
GET  /predict/churn                      Pharmacy churn risk list
GET  /predict/visit-priority             NBA visit order for today
GET  /predict/cross-sell/{id}            Cross-sell basket for one pharmacy
GET  /my/pharmacies                      Delegate's own portfolio
GET  /my/performance                     Delegate's CA vs target
DELETE /cache                            Clear result cache (DIRECTION only)
```

---

## 6. Web Dashboards (4 apps)

Each is an independent Vite + React + TypeScript + Tailwind app. All connect to the same backend.

### direction_web — Executive / Founder Dashboard
**Role:** Global company intelligence  
**Views:** Executive KPIs · Revenue & Finance · Market & Geography · Supply & Stock · People & Delegates · Animations · Forecasts · Anomalies & Alerts · Data Quality  
**API Key:** `fdr-key-2026`

### manager_web — Supervisor / Sales Manager
**Role:** Team and delegate management  
**Views:** Dashboard · Delegates (18) · Coaching Queue · Visit Quality · Anomalies · Semantic Flags · Primes & Bonus · Formation ROI · Attrition Risk  
**API Key:** `sup-key-2026`

### marketing_web — Marketing / Animation Manager
**Role:** Campaign planning and ROI  
**Views:** Dashboard · Animations · Budget ROI · Sentiment Analysis · Themes · Forecasts · Eligibility · Approve / Reject  
**API Key:** `mkt-key-2026`

### shell — Unified Login Shell
**Role:** Entry point that routes to the correct dashboard based on role  
**Features:** JWT login, role-based navigation to manager / marketing / direction views

```
Install & run a single web app:
  cd web/direction_web
  npm install
  npm run dev          # → http://localhost:5173
```

`.env` variables (create in each web app folder):
```
VITE_API_URL=http://localhost:8000
VITE_API_KEY=fdr-key-2026   # change per app
```

---

## 7. Mobile App (React Native)

**Stack:** Expo 54 · React Native 0.79 · expo-router · React 19.0 · TypeScript

**3 role modes** in one APK, selected at login:

| Username prefix | Mode | Navigator |
|-----------------|------|-----------|
| `del*` | Delegate | Bottom tabs: Dashboard · Saisie · Brief · Score · Settings |
| `med*` | Médecin | Bottom tabs: Profil · Historique · Settings |
| `ph*` | Pharmacie | Bottom tabs: Alertes Stock · Analyse · Settings |

**Architecture note:** Each mode wraps its own `NavigationContainer` inside `NavigationIndependentTree` (from `@react-navigation/native`) to prevent conflicts with expo-router's built-in navigator. The root `_layout.tsx` uses `<Slot>` (not `<Stack>`) for the same reason.

**Run:**
```bash
cd mobile
npm install --legacy-peer-deps
npx expo start --clear
# Scan QR in Expo Go — phone + PC must be on same WiFi
```

**IP configuration:** Edit `mobile/src/api/client.ts` line 3:
```typescript
const PC_IP = '192.168.1.XX';  // your machine's local IP
```

---

## 8. AI Chat Assistant

Every screen (web and mobile) has a floating `💬` chat button that opens a context-aware chatbot powered by the real analytics data.

**Endpoint:** `POST /chat`

```json
{
  "message": "Quelles sont mes pharmacies à risque ?",
  "role": "delegate",
  "visit_id": 541
}
```

The backend:
1. Loads cached analytics for the `visit_id`
2. Routes the query by keyword to the correct data section
3. Returns a formatted reply with real numbers from the DB

**Example questions by role:**

| Role | Question | Sample reply |
|------|----------|-------------|
| Delegate | "Mes visites aujourd'hui ?" | "📅 8/12 visites · CA 84% · Tier Excellent" |
| Delegate | "Prédictions prioritaires" | "🎯 Top 5 pharmacies avec scores" |
| Supervisor | "Délégués en sous-performance ?" | "⚠️ 3 délégués sous la moyenne" |
| Marketing | "Quelles animations actives ?" | "🎪 6 animations avec produit + zone" |
| Founder | "CA par zone ?" | "🗺️ 5 zones avec CA détaillé" |

---

## 9. MLOps — Feedback Loop

`feedback_loop.py` implements a lightweight MLOps loop:

```
Prediction made → logged with timestamp + features
       │
       ▼ (30 days later)
Outcome observed (order placed? churn confirmed?)
       │
       ▼
ModelHealthMonitor.validate_outcomes()
  - computes realized AUC vs baseline AUC
  - if drift > 5%: flags model for retraining
       │
       ▼
Retraining queue → triggers optimize_models.py
```

**Drift detection threshold:** AUC drop > 0.05 or R² drop > 0.10 triggers an alert. Models in mode2 (weaker models) are monitored more aggressively.

---

## 10. Setup & Run

### Prerequisites
- Python 3.11+
- Node.js 20+
- MariaDB / MySQL running on port 3307 with database `pharma_db`
- Expo Go app on your phone (for mobile testing)

### Backend

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Start the API
uvicorn api:app --host 0.0.0.0 --port 8000 --reload

# 3. Verify
curl http://localhost:8000/health
```

### Web (run any dashboard)

```bash
cd web/direction_web     # or manager_web / marketing_web / shell
cp .env.example .env     # edit VITE_API_KEY for the role
npm install
npm run dev
```

### Mobile

```bash
cd mobile
npm install --legacy-peer-deps
# Edit src/api/client.ts — set PC_IP to your machine's WiFi IP
npx expo start --clear
```

### Train models (optional — pkl files not in repo)

```bash
python baseline_models.py         # trains 4 baseline RandomForest models
python optimize_models.py         # upgrades to XGBoost + GridSearch
python train_remaining_models.py  # trains models 5-15
python fix_leakage_models.py      # fixes campaign_response + cross_sell leakage
```

---

## Project Structure

```
pii/
├── api.py                      # FastAPI server (1600+ lines)
├── orchestrator.py             # 4-agent ML orchestrator
├── db_layer.py                 # MariaDB abstraction + FeatureBuilder
├── deep_analysis.py            # BI engine (all CRM analytics)
├── baseline_models.py          # Phase 1: RandomForest baselines
├── optimize_models.py          # Phase 2: XGBoost + GridSearch
├── train_remaining_models.py   # Phase 3: Models 5-15
├── fix_leakage_models.py       # Phase 4: Leakage removal
├── feedback_loop.py            # MLOps: drift detection + retraining
├── requirements.txt
├── models/
│   ├── model_registry.json     # Master registry (status, metrics, paths)
│   └── *_features.json         # Feature lists per model
├── mobile/                     # React Native app
│   ├── AppRoot.tsx
│   ├── AppDelegate.js
│   ├── AppMedecin.js
│   ├── AppPharmacie.js
│   └── src/
│       ├── screens/
│       ├── components/         # FloatingChat, DelegateHeader, etc.
│       ├── hooks/              # useDelegateData, useOrchestrator, etc.
│       ├── context/            # SessionContext, ProfileContext
│       └── api/client.ts
└── web/
    ├── direction_web/          # Founder dashboard
    ├── manager_web/            # Supervisor dashboard
    ├── marketing_web/          # Marketing dashboard
    └── shell/                  # Unified login shell
```
