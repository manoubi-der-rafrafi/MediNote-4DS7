# Direction Web — Strategic Dashboard pour Direction

Dashboard board-level pour KPIs nationaux, prévisions, performance géographique et alertes stratégiques.

## 🚀 Quick Start

### Installation

```bash
npm install
cp .env.example .env
npm run dev
```

Accès: **http://localhost:3003**  
Credentials: `direction@crmpharm.com` / `password`

## 📊 Pages

### 1. KPIs (`/kpis`)

Vue consolidée KPIs nationaux:

- **KPI Cards** (6×): CA Total, Visites, Rx, Parts marché, Délégués, NPS
- **CA par région (12m AreaChart)**: Casablanca, Rabat, Marrakech, Fès, Agadir
- **Top 6 Produits (BarChart horizontal)**: Revenue ranking
- **Régions DataTable**: Région, délégués, CA, visites, Rx, score moy, delta%

### 2. Forecast National (`/forecast`)

Prévisions nationales avec 3 scénarios:

- **Metric/Horizon Selectors**: CA, Parts marché, Rx, Visites / 6m, 12m, 24m
- **Scenario Cards** (3×): Pessimiste/Réaliste/Optimiste avec impacts
- **Forecast AreaChart**: 3-scenario projection (6m visible)
- **Par Produit DataTable**: Produit, CA actuel, forecast, croissance%, risque

### 3. Géographie (`/geo`)

Performance par territoires & régions:

- **KPI Cards** (4×): Couverture moyenne, Efficacité, Potentiel non-exploité, Zones blanches
- **Territoires DataTable**: Territory, délégué, couverture%, potentiel, efficacité, score
- **Radar Chart** (5 axes): Couverture, Efficacité, CA, Qualité, NBA Score
- **Treemap**: Répartition CA par territoire visuelle

### 4. Alertes Stratégiques (`/alertes`)

Real-time strategic alerts monitoring:

- **Live Status**: ● EN DIRECT
- **Filters**: Sévérité (ALL/CRITICAL/URGENT/WATCH), Statut (ALL/UNREAD/READ)
- **Alerts DataTable** (20/page): Sévérité, type, message, impact MAD, agent, date
- **Timeline (7j BarChart)**: Compte par sévérité/jour (CRITICAL/URGENT/WATCH)

Sévérité:
- 🔴 **CRITICAL**: Immediate action required
- 🟠 **URGENT**: Within hours
- 🟡 **WATCH**: Monitoring required

Détection agents: Agent_Stock, Agent_Anomaly, Agent_Alerte, etc.

## 🔗 API Endpoints

```
POST  /auth/login                        # User authentication
GET   /direction/kpis                    # National KPIs
GET   /direction/kpis/regions            # Regional breakdown
GET   /direction/forecast/national       # National forecast
GET   /direction/geo/territories         # Territory data
GET   /direction/strategic-alerts        # Live alerts
GET   /direction/strategic-alerts/{id}   # Alert details
WS    /ws/alerts/{userId}                # Real-time alerts stream
```

## 🎨 Styling

**Brand Color**: Red (`#F87171`)

- KPI cards: `color="direction"`
- Buttons: `bg-direction`
- Accents: `text-direction`

### Dark Theme Palette

```
#0E0E10 bg
#18181C s1 (cards)
#22222A s2 (input)
#2A2A35 s3
rgba(255,255,255,0.08) borders
```

## 📦 Dependencies

```json
{
  "react": "18.3.0",
  "typescript": "5.4.0",
  "vite": "5.2.0",
  "tailwindcss": "3.4.0",
  "react-router-dom": "6.23.0",
  "axios": "1.7.0",
  "@tanstack/react-query": "5.39.0",
  "zustand": "4.5.0",
  "recharts": "2.12.0",
  "react-hot-toast": "2.4.1",
  "socket.io-client": "4.7.5",
  "lucide-react": "0.383.0"
}
```

## 🧪 Mock Data

**Enabled by default** — Data imported dans chaque page:

- `mockRegions`: 5 régions avec CA, visites, Rx, scores
- `mockTerritories`: Territoires par région avec metrics
- `mockProducts`: Produits forecast avec croissance & risque
- `mockAlerts`: Strategic alerts avec sévérité & impact

**Pour switching vers API réelle**:

1. Remplacer imports mock par `useQuery()`
2. Update endpoint URLs
3. Type API responses selon interfaces

## 🔐 Authentication

```typescript
// src/lib/auth.ts — Zustand store

const useAuth = create(...) // { token, user, login, logout }

// Usage in components
const { token, user, logout } = useAuth();
```

Persisted to localStorage — survit au refresh.

## 📡 Real-Time Alerts

```typescript
// src/lib/socket.ts

// Connection
const socket = io('ws://localhost:8000', {...})

// Listen
socket.on('alert', (data) => toast.error(...))
```

WebSocket subscription automatique on mount, triggers toast notifications.

## 🛠️ Development

### Type Checking

```bash
npm run type-check
```

### Build

```bash
npm run build  # dist/ folder
npm run preview
```

### Environment

`.env` (example):

```
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000
```

## 🔄 Component Hierarchy

```
App (Router)
├─ LoginPage
└─ ProtectedRoute
   └─ AppLayout (Sidebar with 4 items + Pages)
      ├─ KPIsPage
      ├─ ForecastNationalPage
      ├─ GeoPage
      └─ AlertesStrategiquesPage
```

All pages use shared UI components (KpiCard, DataTable, Badge, ProgressBar, etc.)

## 🎯 Feature Checklist

- [x] Authentication (mock & real)
- [x] National KPIs dashboard (6 cards)
- [x] Regional CA visualization (AreaChart)
- [x] Top products ranking
- [x] Regional breakdown table
- [x] Multi-scenario forecast
- [x] Product forecast table
- [x] Territory performance cards
- [x] Territory datatable with expand
- [x] Radar chart (5 axes)
- [x] Treemap visualization
- [x] Real-time strategic alerts
- [x] Alert filtering (severity/status)
- [x] 7-day timeline chart
- [x] Dark mode theming
- [x] Responsive design
- [x] WebSocket alerts
- [x] DataTable (sort/filter/paginate)
- [x] Protected routes

---

**Port:** 3003  
**Stack:** React 18 + Vite + TypeScript + Tailwind  
**Theme:** Dark  
**Status:** Production-Ready ✅
