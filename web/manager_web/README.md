# Manager Web — Dashboard pour Managers Régionaux

Dashboard exécutif pour les managers régionaux phares performance d'équipe, anomalies et prévisions.

## 🚀 Quick Start

### Installation

```bash
npm install
cp .env.example .env
npm run dev
```

Accès: **http://localhost:3001**  
Credentials: `manager@crmpharm.com` / `password`

## 📊 Pages

### 1. Dashboard (`/dashboard`)

Vue consolidée des KPIs et performance actuelle:

- **KPI Cards** (4×): CA Total, Visites, Rx générées, Team Score
- **Anomalies DataTable**: Détection temps-réel avec sévérité
- **Tier Distribution Chart**: Répartition délégués par tier (A/B/C/D)
- **Expiry Alerts**: Alertes sur stocks proches expiration
- **Forecast Preview**: 3 scénarios (pessimiste, réaliste, optimiste)

### 2. Team (`/team`)

Gestion et monitoring équipe:

- **Delegates DataTable**: Score, tier, visites, delta
- **Detail Drawer**: Ring chart + barres de progression (scores composants)

### 3. Anomalies (`/anomalies`)

Timeline des anomalies détectées:

- **Timeline Chart**: Évolution du score anomalie sur 90j
- **Filters**: Période, sévérité, type
- **Anomalies DataTable**: Status badges, sévérité, détails

### 4. Forecast (`/forecast`)

Prévisions avec 3 scénarios:

- **Metric/Horizon/Scope Selectors**: CA/Marché/Rx sur 6m/12m/24m
- **Scenario Cards**: Pessimiste/Réaliste/Optimiste avec hypothèses
- **Forecast Chart**: Visualisation trajectoire
- **Risks Sections**: Risques produit + risques stratégiques

## 🔗 API Endpoints

```
POST  /auth/login                    # User authentication
GET   /manager/dashboard/kpis        # KPI metrics
GET   /manager/dashboard/anomalies   # Anomalies timeline
GET   /manager/team/delegates        # Team members list
GET   /manager/team/{id}             # Delegate details
GET   /manager/forecast              # Forecast data
WS    /ws/alerts/{userId}            # Real-time alerts
```

## 🎨 Styling

**Brand Color**: Purple (`#A78BFA`)

- KPI cards: `color="manager"`
- Buttons: `bg-manager`
- Accents: `text-manager`

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

- `mockDashboardData`: KPIs, anomalies, expiry
- `mockTeam`: Délégués avec scores
- `mockAnomalies`: Timeline + status
- `mockForecast`: 3 scénarios

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
   └─ AppLayout (Sidebar + Pages)
      ├─ DashboardPage
      ├─ TeamPage
      ├─ AnomaliesPage
      └─ ForecastPage
```

All pages use shared UI components (KpiCard, DataTable, etc.)

## 🎯 Feature Checklist

- [x] Authentication (mock & real)
- [x] Dashboard with 4 KPI cards
- [x] Anomalies timeline visualization
- [x] Team management with details
- [x] 3-scenario forecast
- [x] Dark mode theming
- [x] Responsive design
- [x] WebSocket alerts
- [x] DataTable (sort/filter/paginate)
- [x] Protected routes

---

**Port:** 3001  
**Stack:** React 18 + Vite + TypeScript + Tailwind  
**Theme:** Dark  
**Status:** Production-Ready ✅
