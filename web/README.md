# CRM Pharma — Web Interfaces

Vue consolidée multirôle du système CRM pour le secteur pharmaceutique marocain.

## 📋 Architecture

Trois applications web indépendantes basées sur **React 18 + Vite + TypeScript** :

| App | Port | Audience | Accès |
|-----|------|----------|-------|
| **manager_web** | 3001 | Regional Managers | Tableau de bord performance équipe |
| **marketing_web** | 3002 | Marketing Team | Analyse segments & sentiment NLP |
| **direction_web** | 3003 | Direction/Board | KPIs nationaux & strategic alerts |

## 🚀 Installation

### Prérequis

- **Node.js** 18+ et **npm** 9+
- **Backend API** running sur `http://localhost:8000/api/v1`
- Terminal/PowerShell avec accès au répertoire `web/`

### Étape 1: Cloner les dépendances

```bash
cd web/

# Installation manager_web
cd manager_web
npm install
cd ..

# Installation marketing_web
cd marketing_web
npm install
cd ..

# Installation direction_web
cd direction_web
npm install
cd ..
```

### Étape 2: Configuration environnement

Pour chaque app (manager_web, marketing_web, direction_web):

```bash
cp .env.example .env
```

**Variables d'environnement requises** (`.env`) :

```
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000
```

## 🎯 Démarrage des applications

### Terminal 1: Manager Dashboard

```bash
cd web/manager_web
npm run dev
```

Accès: `http://localhost:3001`  
Credentials: `manager@crmpharm.com` / `password`

### Terminal 2: Marketing Dashboard

```bash
cd web/marketing_web
npm run dev
```

Accès: `http://localhost:3002`  
Credentials: `marketing@crmpharm.com` / `password`

### Terminal 3: Direction Dashboard

```bash
cd web/direction_web
npm run dev
```

Accès: `http://localhost:3003`  
Credentials: `direction@crmpharm.com` / `password`

## 📦 Stack Techniques

### Core Framework
- **React** 18.3.0 — UI rendering
- **TypeScript** 5.4.0 — Type safety (strict mode)
- **Vite** 5.2.0 — Build & dev server (HMR)
- **React Router DOM** 6.23.0 — Navigation & routing

### Styling & UI
- **Tailwind CSS** 3.4.0 — Utility-first styling
- **Lucide React** 0.383.0 — Icon library

### Data & State
- **Axios** 1.7.0 — HTTP client with interceptors
- **@tanstack/react-query** 5.39.0 — Server state management
- **Zustand** 4.5.0 — Client state (auth)
- **Socket.io-client** 4.7.5 — WebSocket real-time alerts

### Visualization
- **Recharts** 2.12.0 — Data visualization (AreaChart, BarChart, LineChart, PieChart, RadarChart)
- **React Hot Toast** 2.4.1 — Notifications

## 🎨 Design System

### Palette Globale

```
Background:     #0E0E10
Surface 1:      #18181C
Surface 2:      #22222A
Surface 3:      #2A2A35
Border:         rgba(255,255,255,0.08)

Accents:
  manager:      #A78BFA (purple)
  marketing:    #FB923C (orange)
  direction:    #F87171 (red)

Utilities:
  success:      #34D399 (green)
  warning:      #FBBF24 (gold)
  danger:       #F87171 (red)
  info:         #4F8EF7 (blue)
  teal:         #2DD4BF
```

### Composants Partagés

- **KpiCard** — Affichage KPI avec delta
- **RingChart** — Progress ring SVG
- **Badge** — Statut/sévérité
- **DataTable** — Tableau avec sort/filter/pagination
- **ProgressBar** — Barre de progression
- **PageHeader** — Titre + sous-titre + action
- **Sidebar** — Navigation app-spécifique
- **AlertBanner** — Alerte avec priorité

## 📡 API Endpoints

### Authentication
- `POST /auth/login` — Login (user, password)
- `POST /auth/logout` — Logout

### Manager Dashboard
- `GET /manager/kpis` — KPIs
- `GET /manager/team` — Delegates
- `GET /manager/anomalies` — Timeline
- `GET /manager/forecast` — Predictions

### Marketing Dashboard
- `GET /marketing/segments` — Segment metrics
- `GET /marketing/sentiment` — NLP flags & scores
- `GET /marketing/roi` — Campaign ROI

### Direction Dashboard
- `GET /direction/kpis` — National KPIs
- `GET /direction/forecast/national` — Forecast
- `GET /direction/geo/territories` — Territory data
- `GET /direction/strategic-alerts` — Live alerts

### WebSocket
- `ws://localhost:8000/ws/alerts/{userId}` — Real-time alerts

## 📝 Development Commands

### Per App

```bash
# Development server (HMR enabled)
npm run dev

# Type check
npm run type-check

# Build for production
npm run build

# Preview production build
npm run preview

# Linting (if configured)
npm run lint
```

## 🔐 Authentication Flow

1. User accesse `/login`
2. Submit credentials → `POST /auth/login`
3. Backend retourne `{ token, user }`
4. Token stocké en `localStorage` et injected en header `Authorization: Bearer {token}`
5. 401 response → redirect `/login`
6. ProtectedRoute wrapper valide token

## 🧪 Testing

### Mock Data

Les 3 apps utilisent **mock data** en ligne dans les pages (fichiers `.tsx`) :

- Manager: `mockDashboardData`, `mockAnomalies`, `mockTeam`
- Marketing: `mockSegments`, `mockAnimations`, `mockRoiData`
- Direction: `mockRegions`, `mockTerritories`, `mockAlerts`

Pour intégration API réelle, remplacer les imports mock par des `useQuery()` calls vers les endpoints.

### Recharts Dark Mode

Tous les charts appliquent custom styling pour dark theme:

```typescript
<CartesianGrid strokeDasharray="3 3" stroke="#2A2A35" />
<XAxis stroke="#A0A0B0" />
<YAxis stroke="#A0A0B0" />
```

## 🐛 Troubleshooting

### Port déjà utilisé

Si port 3001/3002/3003 en utilisation:

```bash
# Windows — Find process
netstat -ano | findstr :3001

# Kill process
taskkill /PID <PID> /F

# Or change VITE port in vite.config.ts
# server: { port: 3004 }
```

### 401 Unauthorized

- Vérifier que backend API tourne sur `localhost:8000`
- Vérifier credentials (voir section "Démarrage")
- Token expiré? Logout + re-login

### WebSocket connection refused

- Backend doit exposer endpoint `/ws/alerts/{userId}`
- Vérifier `VITE_WS_URL` en `.env`

### Build errors TypeScript

```bash
npm run type-check
# Fix types then retry npm run build
```

## 📦 Project Structure

```
web/
├── manager_web/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/           # KpiCard, Badge, DataTable...
│   │   │   └── layout/       # AppLayout, Sidebar
│   │   ├── lib/              # api.ts, auth.ts, socket.ts
│   │   ├── pages/            # Dashboard, Team, Anomalies, Forecast
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── tsconfig.json
│
├── marketing_web/            # Structure identique
│   ├── src/pages/            # Segments, Sentiment, ROI
│   └── ...
│
├── direction_web/            # Structure identique
│   ├── src/pages/            # KPIs, Forecast, Geo, Alertes
│   └── ...
└── README.md
```

## 🔄 Integration Checklist

- [ ] Backend API running & accessible
- [ ] All 3 apps npm install complete
- [ ] `.env` files created & configured
- [ ] `npm run dev` working on all 3 ports
- [ ] Login credentials working
- [ ] WebSocket connection successful
- [ ] Mock data displaying correctly
- [ ] Replace mock data with real API calls (integration phase)

## 📞 Support

Pour questions/issues:

1. Vérifier port & connectivity
2. Check Node.js/npm versions: `node -v`, `npm -v`
3. Clear node_modules & reinstall: `rm -r node_modules && npm install`
4. Check environment variables (VITE_API_URL, VITE_WS_URL)

---

**Generated:** 2026-04-14  
**Stack:** React 18 + Vite 5 + TypeScript 5 + Tailwind 3  
**Agents:** Manager · Marketing · Direction
