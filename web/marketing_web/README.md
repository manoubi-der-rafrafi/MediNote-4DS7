# Marketing Web — Dashboard pour Équipe Marketing

Dashboard pour analyse segments, sentiment NLP et ROI campagnes.

## 🚀 Quick Start

### Installation

```bash
npm install
cp .env.example .env
npm run dev
```

Accès: **http://localhost:3002**  
Credentials: `marketing@crmpharm.com` / `password`

## 📊 Pages

### 1. Segments (`/segments`)

Analyse détaillée des segments d'entités:

- **View Toggle**: Médecins (420 entities, 4 segments) vs Pharmacies (150 entities, 4 segments)
- **Ring Charts** (4×): HIGH_POTENTIAL, LOYAL, AT_RISK, DORMANT
- **Pie Chart**: Distribution visuelle par segment
- **Entities DataTable**: Segment badges, metrics, actions

Segments breakdown:
- **HIGH_POTENTIAL** (GREEN): Croissance forte, engagement élevé
- **LOYAL** (BLUE): Revenu stable, retention élevée
- **AT_RISK** (ORANGE): Engagement baisse, churn risk
- **DORMANT** (GRAY): Inactifs, re-engagement needed

### 2. Sentiment (`/sentiment`)

NLP sentiment analysis depuis commentaires:

- **Period Selector**: 7j, 30j, 90j
- **Global Sentiment Ring**: % positif (ex: 74%)
- **Sentiment Trend Chart**: Evolution over period
- **8 NLP Flags Breakdown**: Progress bars pour Satisfaction, Qualité, Prix, etc.
- **Animations DataTable**: Sentiment score + flags présents

Flags NLP:
1. Satisfaction
2. Qualité
3. Prix
4. Disponibilité
5. Délai livraison
6. Service client
7. Recommandation
8. Problem resolution

### 3. ROI (`/roi`)

Campaign performance & ROI tracking:

- **Campaign Selector**: Dropdown list
- **KPI Cards** (3×): ROI %, CA généré, Coût campagne
- **Before/After BarChart**: CA grouped par période
- **Regional ROI BarChart**: ROI% horizontal par région
- **Animations DataTable**: DetailS campagne avec verdicts

## 🔗 API Endpoints

```
POST  /auth/login                    # User authentication
GET   /marketing/segments            # Segment metrics
GET   /marketing/segments/medecins   # Doctors data
GET   /marketing/segments/pharmacies # Pharmacies data
GET   /marketing/sentiment           # NLP sentiment
GET   /marketing/roi/campaigns       # Campaign list
GET   /marketing/roi/{campaignId}    # Campaign details
WS    /ws/alerts/{userId}            # Real-time alerts
```

## 🎨 Styling

**Brand Color**: Orange (`#FB923C`)

- KPI cards: `color="marketing"`
- Buttons: `bg-marketing`
- Accents: `text-marketing`

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

- `mockSegments`: Médecins & Pharmacies breakdown
- `mockAnimations`: NLP flags & sentiment scores
- `mockRoiData`: Campaign data avec Before/After

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
      ├─ SegmentsPage
      ├─ SentimentPage
      └─ ROIPage
```

All pages use shared UI components (KpiCard, DataTable, CustomPieChart, etc.)

## 🎯 Feature Checklist

- [x] Authentication (mock & real)
- [x] Segments analysis (Médecins/Pharmacies)
- [x] Ring charts for segment distribution
- [x] Pie chart visualization
- [x] NLP sentiment tracking
- [x] Sentiment trends
- [x] NLP flags breakdown
- [x] Campaign ROI tracking
- [x] Before/After comparison
- [x] Regional ROI breakdown
- [x] Dark mode theming
- [x] Responsive design
- [x] WebSocket alerts
- [x] DataTable (sort/filter/paginate)
- [x] Protected routes

---

**Port:** 3002  
**Stack:** React 18 + Vite + TypeScript + Tailwind  
**Theme:** Dark  
**Status:** Production-Ready ✅
