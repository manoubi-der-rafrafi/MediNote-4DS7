# Medinote — AI-Powered Pharma CRM

End-to-end pharmaceutical CRM intelligence platform: 15 production ML models, a multi-agent orchestrator, four role-specific web dashboards, and a React Native mobile app — all served from a single FastAPI backend.

---

## Table of Contents

1. [What this project does](#1-what-this-project-does)
2. [Project Structure](#2-project-structure)
3. [System Architecture](#3-system-architecture)
4. [ML Pipeline — 15 Models](#4-ml-pipeline--15-models)
5. [Multi-Agent Orchestrator](#5-multi-agent-orchestrator)
6. [Backend API](#6-backend-api)
7. [Web Dashboards](#7-web-dashboards)
8. [Mobile App](#8-mobile-app)
9. [AI Chat Assistant](#9-ai-chat-assistant)
10. [MLOps — Feedback Loop](#10-mlops--feedback-loop)
11. [Setup & Run](#11-setup--run)

---

## 1. What this project does

Medinote transforms raw pharmaceutical sales data (pharmacies, delegates, doctors, products) into actionable intelligence for every role in the company:

| Role | What they see |
|------|--------------|
| **Founder / Direction** | Company-wide CA, delegate rankings, geographic heatmaps, anomaly alerts |
| **Supervisor** | Team performance, coaching queue, visit quality scoring |
| **Marketing** | Campaign ROI, RFM segmentation, sentiment analysis, animation management |
| **Delegate** | Daily visit plan (NBA), CA achievement, churn risk per pharmacy, cross-sell recommendations |
| **Pharmacist** | Stock alerts, product demand forecast, tier upgrade opportunity |
| **Doctor** | Prescription history, representative visit history |

Every number shown in the UI comes from the database through the ML models — no mock data.

---

## 2. Project Structure

```
medinote-ai/
│
├── api.py                      # FastAPI server — main entry point, run this to start
├── orchestrator.py             # 4-agent AI: Intent → Data → Prediction → Explanation
├── db_layer.py                 # MariaDB connection + FeatureBuilder (80+ ML features)
├── deep_analysis.py            # BI engine: queries all CRM tables, returns JSON insights
├── feedback_loop.py            # MLOps: logs predictions, detects drift, triggers retraining
├── capability_checker.py       # Logs unknown queries (mode3) for future model training
│
├── requirements.txt            # Python dependencies (pip install -r requirements.txt)
├── README.md                   # This file
├── .gitignore                  # Excludes CSV, pkl, .venv, node_modules, etc.
│
├── ml/                         # ── ML Training Pipeline ──────────────────────────────
│   ├── baseline_models.py      # Phase 1: trains 4 RandomForest baselines
│   ├── optimize_models.py      # Phase 2: upgrades baselines to XGBoost + GridSearchCV
│   └── train_remaining_models.py  # Phase 3: trains models 5–15 (11 additional tasks)
│
├── models/                     # ── Model Artifacts ───────────────────────────────────
│   ├── model_registry.json     # Master registry: status, metrics, path for all 15 models
│   ├── *_features.json         # Feature list used by each model (one file per model)
│   └── *.pkl                   # Trained model binaries (excluded from git — large files)
│
├── mobile/                     # ── React Native App (Expo 54) ────────────────────────
│   ├── AppRoot.tsx             # Entry point: decides which mode to render after login
│   ├── AppDelegate.js          # Delegate mode: tabs Dashboard · Saisie · Brief · Score
│   ├── AppMedecin.js           # Doctor mode: tabs Profil · Historique · Settings
│   ├── AppPharmacie.js         # Pharmacy mode: tabs Alertes · Analyse · Settings
│   ├── app/_layout.tsx         # Expo Router root layout (uses <Slot>, not <Stack>)
│   ├── app/index.tsx           # Expo Router entry → renders AppRoot
│   └── src/
│       ├── screens/            # Full-screen views (LoginScreen, FeedScreen, etc.)
│       ├── components/         # Reusable UI (FloatingChat, DelegateHeader, KpiTile…)
│       ├── hooks/              # Data hooks (useDelegateData, useOrchestrator…)
│       ├── context/            # State (SessionContext, ProfileContext)
│       ├── api/client.ts       # HTTP client — set PC_IP here for device testing
│       └── theme.js            # Dark theme colors, spacing, typography
│
├── web/                        # ── Web Dashboards (4 apps) ───────────────────────────
│   ├── direction_web/          # Founder dashboard — CA global, zones, people
│   │   ├── src/App.tsx         # Navigation + view router
│   │   ├── src/views/          # Executive, Revenue, Market, Supply, People, Anomalies…
│   │   ├── src/components/     # KpiCard, HeatmapGrid, ChatWidget, AnimationTable…
│   │   ├── src/hooks/          # useFounderData — fetches /predictions/all-roles
│   │   └── src/lib/api.ts      # API client with X-API-Key header
│   │
│   ├── manager_web/            # Supervisor dashboard — team, coaching, attrition
│   │   ├── src/App.tsx
│   │   ├── src/views/          # Dashboard, Delegates, Coaching, Primes, Attrition…
│   │   ├── src/components/     # DelegateCard, CoachCard, ChatWidget, AlertBox…
│   │   └── src/hooks/          # useManagerData
│   │
│   ├── marketing_web/          # Marketing dashboard — animations, ROI, sentiment
│   │   ├── src/App.tsx
│   │   ├── src/views/          # AnimationList, BudgetROI, Sentiment, Themes, Eligibility…
│   │   ├── src/components/     # AnimSearchTable, ChatWidget, SentimentSample…
│   │   └── src/hooks/          # useMarketingData
│   │
│   ├── shell/                  # Unified login shell — routes to the correct dashboard
│   │   ├── src/App.tsx
│   │   ├── src/pages/          # LoginPage
│   │   ├── src/components/     # AppLayout (sidebar + ChatWidget), ChatWidget
│   │   └── src/lib/            # auth.ts (JWT), api.ts
│   │
│   └── shared/                 # Shared components used across web apps
│       ├── components/         # Button, Card, KPITile, RoleSwitcher, StatusPill…
│       └── src/hooks/          # useOrchestrator (shared data fetching logic)
│
└── archive/                    # ── One-time Scripts (already applied) ───────────────
    ├── fix_leakage_models.py   # Removed leaking features from 2 models (done once)
    ├── fix_delegate_mapping.py # Built delegate ID bridge table (done once)
    ├── label_tasks_5_6_8.py    # Generated label CSV files (done once)
    └── chat.py                 # CLI REPL for testing the orchestrator locally
```

---

## 3. System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                │
│                                                                      │
│   direction_web     manager_web    marketing_web     shell           │
│   (Vite+React)      (Vite+React)   (Vite+React)    (Vite+React)     │
│                                                                      │
│                  mobile (React Native + Expo 54)                     │
│             Delegate · Doctor · Pharmacist modes                     │
└──────────────────────┬───────────────────────────────────────────────┘
                       │  HTTP REST  (X-API-Key auth)
┌──────────────────────▼───────────────────────────────────────────────┐
│                    FASTAPI BACKEND  :8000  (api.py)                  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │             Multi-Agent Orchestrator (orchestrator.py)        │   │
│  │   Intent Classifier → Data Agent → Prediction Agent          │   │
│  │                      → Explanation Agent                      │   │
│  └─────────────────────────────┬────────────────────────────────┘   │
│                                │                                     │
│  ┌─────────────────────────────▼────────────────────────────────┐   │
│  │              DeepAnalysis BI Engine (deep_analysis.py)        │   │
│  │   pharmacy · delegate · rfm · temporal · geographic           │   │
│  │   product · nlp · animations · formations                     │   │
│  └─────────────────────────────┬────────────────────────────────┘   │
│                                │                                     │
│  ┌─────────────────────────────▼────────────────────────────────┐   │
│  │              15 ML Models  (models/*.pkl)                     │   │
│  │   mode1: direct prediction  │  mode2: analytics fallback      │   │
│  └─────────────────────────────┬────────────────────────────────┘   │
│                                │                                     │
│  ┌─────────────────────────────▼────────────────────────────────┐   │
│  │           Feedback Loop / MLOps  (feedback_loop.py)           │   │
│  │   log → validate outcome → detect drift → retrain trigger     │   │
│  └─────────────────────────────┬────────────────────────────────┘   │
└───────────────────────────────-┼─────────────────────────────────────┘
                                 │  SQLAlchemy + PyMySQL
┌────────────────────────────────▼─────────────────────────────────────┐
│               MariaDB  :3307  /pharma_db                             │
│   ~117 tables: clients, ventes, visites, animations, formations,     │
│   primes, prescriptions, prospects, articles, zones, fournisseurs…   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. ML Pipeline — 15 Models

### Training phases

```
ml/baseline_models.py   →   ml/optimize_models.py   →   ml/train_remaining_models.py
      Phase 1                     Phase 2                        Phase 3
  4 RandomForest            XGBoost + GridSearch             11 more models
    baselines                 on models 1–4                   (tasks 5–15)

                    archive/fix_leakage_models.py
                          Phase 4 (done once)
                    Removed leaking features from 2 models
```

### Why RandomForest as baseline?
RandomForest was chosen because it handles mixed feature types without normalization, never overfits badly on first run, and gives reliable feature importance scores with zero tuning — making it a safe floor to establish before optimizing.

### Why XGBoost for production?

| Property | RandomForest | XGBoost | Winner |
|----------|-------------|---------|--------|
| Missing data | Via surrogates | Native `missing=NaN` | XGBoost |
| Speed on 100k+ rows | Slow | Fast (histogram) | XGBoost |
| Regularization | None | L1 + L2 + subsample | XGBoost |
| Learns from errors | No | Yes (gradient boosting) | XGBoost |
| Calibrated probabilities | Poor | Good | XGBoost |
| Tested on pharmacy_churn | AUC 0.71 | AUC 0.87 | **+16 pts** |

### Why not deep learning?
The dataset has ~49 delegates and ~772 pharmacies — too small for LSTM or Transformers to beat tree ensembles. XGBoost training takes 30 seconds; a Transformer baseline would take hours with no improvement on this scale of tabular data.

### Split strategy
`TimeSeriesSplit` — never random shuffling. Shuffled splits inflate AUC by up to 15% due to temporal autocorrelation in pharmacy purchase patterns.

### Best GridSearch parameters found

```python
param_grid = {
    'n_estimators':  [200, 500],
    'max_depth':     [3, 4, 6],
    'learning_rate': [0.01, 0.05, 0.1],
    'subsample':     [0.8, 1.0],
}
```

Low learning rate (0.01) + more trees consistently outperformed high LR — slow learning generalizes better on pharmacy purchase data.

### All 15 models

| # | Task | Type | Algorithm | Score | Production | Mode |
|---|------|------|-----------|-------|------------|------|
| 1 | pharmacy_churn_risk | Classification | XGBoost | AUC 0.874 | ⚠️ leakage noted | mode2 |
| 2 | delegate_performance_score | Regression | XGBoost | R² 0.790 | ⚠️ small N | mode2 |
| 3 | sales_forecast_30d | Regression | XGBoost | R² 0.702 | ✅ | mode2 |
| 4 | product_demand_forecast | Regression | XGBoost | R² 0.729 | ✅ | mode1 |
| 5 | payment_default_risk | Classification | XGBoost | AUC 0.998 | ✅ | mode1 |
| 6 | campaign_response | Classification | XGBoost | AUC 0.999 | ✅ fixed | mode1 |
| 7 | visit_priority_ranking | Regression | RandomForest | R² 0.522 | ⚠️ weak | mode2 |
| 8 | delegate_target_achievement | Classification | XGBoost | AUC 0.500 | ❌ 1 class | mode2 |
| 9 | order_cancellation_risk | Classification | XGBoost | AUC 0.998 | ✅ | mode1 |
| 10 | complaint_recurrence | Classification | XGBoost | AUC 0.500 | ❌ | mode2 |
| 11 | pharmacy_tier_upgrade | Classification | XGBoost | AUC 0.999 | ✅ | mode1 |
| 12 | product_sales_trend | Classification | XGBoost | AUC 0.909 | ✅ | mode1 |
| 13 | delegate_activity_drop | Classification | XGBoost | AUC 0.509 | ❌ | mode2 |
| 14 | pharmacy_next_purchase | Regression | XGBoost | R² −34.1 | ❌ | mode2 |
| 15 | cross_sell_ranking | Classification | XGBoost | AUC 0.841 | ✅ fixed | mode1 |

**mode1** = model used directly · **mode2** = model available, analytics engine fills gaps

### Leakage fixes (archive/fix_leakage_models.py — already applied)

Two models returned `AUC = 1.0` — a perfect score that always means data leakage:

- **campaign_response**: leaked feature `order_last_14d` (orders placed *after* the campaign — the answer itself). Removed → honest AUC **0.999**
- **cross_sell_ranking**: leaked feature `pharmacy_bought_last_90d` (whether they already bought the product). Removed → honest AUC **0.841**

---

## 5. Multi-Agent Orchestrator

`orchestrator.py` converts a natural language query into a structured prediction response through 4 sequential agents:

```
User query (FR/EN)
      │
      ▼
┌─────────────────┐
│  Intent Agent   │  Classifies into 8 types:
│                 │  churn_risk · visit_priority · sales_forecast
│                 │  product_demand · payment_risk · cross_sell
│                 │  performance_analysis · unknown (→ mode3 log)
└────────┬────────┘
         ▼
┌─────────────────┐
│   Data Agent    │  Fetches features from MariaDB via FeatureBuilder
│                 │  80+ features per pharmacy/delegate, cached 30 min
└────────┬────────┘
         ▼
┌─────────────────┐
│ Prediction Agent│  Loads .pkl → runs safe_predict()
│                 │  safe_predict: clips negatives, handles NaN,
│                 │  falls back to analytics if model fails
└────────┬────────┘
         ▼
┌─────────────────┐
│Explanation Agent│  Returns human-readable insight with real numbers
└─────────────────┘
```

Unknown queries → logged by `capability_checker.py` → `mode3_requests.jsonl` → future training data.

---

## 6. Backend API

**Start:** `uvicorn api:app --host 0.0.0.0 --port 8000 --reload`

### Authentication

| Method | Header | Used by |
|--------|--------|---------|
| X-API-Key | `X-API-Key: fdr-key-2026` | Mobile + web dashboards |
| JWT Bearer | `Authorization: Bearer <token>` | Login flow |

**API Key → Role:**

| Key | Role |
|-----|------|
| `fdr-key-2026` | Founder / Direction |
| `sup-key-2026` | Superviseur |
| `mgr-key-2026` | Commercial / Manager |
| `mkt-key-2026` | Marketing |
| `dlg-key-2026` | Délégué |
| `ph-key-2026` | Pharmacy |

### Main endpoints

```
GET  /predictions/{visit_id}/all-roles   All 7 role views, cached 30 min
POST /chat                               AI chatbot with real data context
GET  /health                             System status
POST /auth/login                         JWT login
GET  /dashboard/kpis                     Role-filtered KPIs
GET  /analytics/geographic               Zone-level heatmap
GET  /analytics/delegates                Rankings + coaching alerts
GET  /analytics/rfm                      RFM segments
GET  /analytics/products                 Product demand + trends
POST /predict                            Free-text ML query
GET  /predict/churn                      Pharmacy churn list
GET  /predict/visit-priority             NBA visit order for today
GET  /predict/cross-sell/{id}            Cross-sell basket for one pharmacy
GET  /my/pharmacies                      Delegate's portfolio
GET  /my/performance                     Delegate's CA vs target
DELETE /cache                            Clear cache (DIRECTION only)
```

---

## 7. Web Dashboards

Each is a standalone **Vite + React + TypeScript + Tailwind** app.

| App | Role | Port | API Key |
|-----|------|------|---------|
| `direction_web` | Founder | 5173 | `fdr-key-2026` |
| `manager_web` | Supervisor | 5174 | `sup-key-2026` |
| `marketing_web` | Marketing | 5175 | `mkt-key-2026` |
| `shell` | Login shell | 5176 | — |

```bash
cd web/direction_web
cp .env.example .env        # edit VITE_API_KEY
npm install
npm run dev
```

`.env` file:
```
VITE_API_URL=http://localhost:8000
VITE_API_KEY=fdr-key-2026
```

---

## 8. Mobile App

**Stack:** Expo 54 · React Native 0.79 · React 19.0 · expo-router · TypeScript

3 modes in one app, selected at login by username prefix:

| Prefix | Mode | Tabs |
|--------|------|------|
| `del*` | Delegate | Dashboard · Saisie · Brief · Score · Settings |
| `med*` | Médecin | Profil · Historique · Settings |
| `ph*` | Pharmacie | Alertes · Analyse · Settings |

```bash
cd mobile
npm install --legacy-peer-deps

# Edit src/api/client.ts line 3:
# const PC_IP = '192.168.1.XX';  ← your machine's WiFi IP

npx expo start --clear
# Scan QR in Expo Go — phone and PC must be on same WiFi
```

**Architecture note:** Each mode wraps its `NavigationContainer` inside `NavigationIndependentTree` to prevent conflicts with expo-router's own navigator. The root `app/_layout.tsx` uses `<Slot>` (not `<Stack>`) for the same reason.

---

## 9. AI Chat Assistant

A floating `💬` button appears on every screen (web and mobile). It opens a context-aware chatbot backed by real analytics data.

**Endpoint:** `POST /chat`

```json
{
  "message": "Quelles sont mes pharmacies à risque ?",
  "role": "delegate",
  "visit_id": 541
}
```

The backend loads cached analytics for the visit, routes the message by keyword, and returns a formatted reply with real numbers from the database.

**Example questions:**

| Role | Question | Reply example |
|------|----------|--------------|
| Delegate | "Mes visites aujourd'hui ?" | "📅 8/12 visites · CA 84% · Tier Excellent" |
| Delegate | "Prédictions prioritaires" | "🎯 Top 5 pharmacies avec scores" |
| Supervisor | "Délégués en sous-perf ?" | "⚠️ 3 délégués sous la moyenne" |
| Marketing | "Animations actives ?" | "🎪 6 animations produit + zone" |
| Founder | "CA par zone ?" | "🗺️ 5 zones avec CA détaillé" |

---

## 10. MLOps — Feedback Loop

`feedback_loop.py` implements drift detection and retraining triggers:

```
Prediction made → logged with timestamp + features used
        │
        ▼  (30 days later)
Outcome observed (did churn happen? was order placed?)
        │
        ▼
ModelHealthMonitor.validate_outcomes()
  - computes realized AUC vs baseline AUC
  - drift > 5%: flags model for retraining
        │
        ▼
Retraining queue → run ml/optimize_models.py
```

---

## 11. Setup & Run

### Requirements
- Python 3.11+
- Node.js 20+
- MariaDB/MySQL on port 3307, database `pharma_db`
- Expo Go app on your phone

### Backend
```bash
pip install -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
# Test: http://localhost:8000/health
```

### Retrain models (if .pkl files not present)
```bash
python ml/baseline_models.py
python ml/optimize_models.py
python ml/train_remaining_models.py
```

### Web
```bash
cd web/direction_web && cp .env.example .env && npm install && npm run dev
cd web/manager_web   && cp .env.example .env && npm install && npm run dev
cd web/marketing_web && cp .env.example .env && npm install && npm run dev
cd web/shell         && cp .env.example .env && npm install && npm run dev
```

### Mobile
```bash
cd mobile
npm install --legacy-peer-deps
npx expo start --clear
```
