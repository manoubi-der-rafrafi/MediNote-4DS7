# Web Apps → Orchestrator Integration Guide

## Quick Start

All three web apps (direction_web, manager_web, marketing_web) are now wired to the FastAPI orchestrator on `http://localhost:8000`.

### For Each App:

**1. Import the hook (already created for you):**
```tsx
import { useFounderData } from '../hooks/useFounderData';      // direction_web
import { useManagerData } from '../hooks/useManagerData';      // manager_web
import { useMarketingData } from '../hooks/useMarketingData';  // marketing_web
```

**2. Use in your component:**
```tsx
export default function YourView() {
  const {
    kpis,           // extract field you need
    revenue,
    delegateScores,
    loading,
    error,
    refetch,
  } = useFounderData(123);  // 123 = visit_id (default for dev)

  if (loading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;

  // Replace hardcoded data with `kpis`, `revenue`, etc.
  return <YourUI data={kpis} />;
}
```

---

## API Keys (Automatically Injected)

Each app sends its role API key on every request:

- **direction_web** → `X-API-Key: fdr-key-2026` (founder)
- **manager_web** → `X-API-Key: sup-key-2026` (supervisor)
- **marketing_web** → `X-API-Key: mkt-key-2026` (marketing)

---

## Caching Strategy

Backend caches for **30 minutes** via TTL. The shared `useOrchestrator` hook also caches client-side for 30 minutes, so:

- **First call**: ~8.5s (full pipeline)
- **Subsequent calls (within 30 min)**: ~50ms (client cache)
- **After 30 min**: Backend cache expires, refetches from pipeline

To force refresh: call `refetch()` from hook return value.

---

## Response Shape

All hooks return an object like:

```tsx
{
  // Main data (role-specific keys below)
  kpis: {...},
  revenue: {...},
  delegates: [...],
  // ... more fields per role
  
  // Metadata
  orchestratorResponse: {...},      // Full API response
  visitId: 123,
  executionTime: 8.29,              // seconds
  fromCache: false,                 // true if cached
  timestamp: "2026-04-19T10:30:00Z",
  
  // State
  loading: false,
  error: null,
  refetch: () => void,
}
```

---

## Direction Web (Founder Role)

### Available Fields:
- `kpis` - Executive KPIs
- `executive` - High-level metrics
- `revenue` - Financial data
- `market` - Geographic/market analysis
- `supply` - Inventory data
- `people` - Delegate metrics
- `animations` - Animation events
- `forecasts` - Forecast data
- `anomalies` - Alerts & anomalies
- `dataQuality` - Data completeness
- `riskSynthesis` - Risk scoring
- `alerts` - Alerte agent output
- `compliance` - Compliance issues
- `finance` - Finance agent output

### Views to Update:
- Executive.tsx → use `kpis`, `revenue`, `anomalies`
- Revenue.tsx → use `revenue`, `finance`
- Market.tsx → use `market`
- Supply.tsx → use `supply`
- People.tsx → use `people`, `delegateScores`
- Animations.tsx → use `animations`
- Forecasts.tsx → use `forecasts`
- Anomalies.tsx → use `anomalies`, `alerts`
- DataQuality.tsx → use `dataQuality`

---

## Manager Web (Supervisor Role)

### Available Fields:
- `delegates` - All delegates list
- `delegateScores` - Performance scores
- `delegateCoaching` - Coaching plans
- `delegateAnomalies` - Delegate-specific anomalies
- `forecastData` - Forecast for coaching
- `performanceMetrics` - Team performance
- `riskSynthesis` - Risk dashboard

### Views to Update:
- DashboardPage_Manager.tsx → use `delegates`, `delegateScores`, `delegateAnomalies`
- TeamPage.tsx → use `delegates`, `performanceMetrics`
- ForecastPage.tsx → use `forecastData`
- AnomaliesPage.tsx → use `delegateAnomalies`

### Also Delete:
- ~~web/manager_web/src/data/delegates.ts~~ (mock data, no longer needed)

---

## Marketing Web (Marketing Role)

### Available Fields:
- `animations` - Animation events & budgets
- `budgetROI` - Budget allocation & ROI
- `eligibilityData` - Eligibility rules
- `forecastData` - Marketing forecast
- `sentimentAnalysis` - NLP sentiment from comments
- `themes` - Theme analysis
- `roiAnalysis` - ROI by animation/channel
- `nlpInsights` - NLP agent output

### Views to Update:
- ROIPage.tsx → use `budgetROI`, `roiAnalysis`
- SegmentsPage.tsx → use `eligibilityData`
- SentimentPage.tsx → use `sentimentAnalysis`, `nlpInsights`

---

## Full Response Example

```json
{
  "visit_id": 123,
  "timestamp": "2026-04-19T10:30:00Z",
  "execution_time_sec": 8.29,
  "from_cache": false,
  "roles": {
    "founder": {
      "kpis": {
        "total_ca": 209000000,
        "prime_realization_pct": 53.4,
        "budget_execution_pct": 35.3
      },
      "revenue": {...},
      "anomalies": [...]
    },
    "supervisor": {
      "delegates": [
        {"id_delegate": 1, "name": "Amor Khelifi", "score": 85}
      ],
      "delegateScores": [...]
    },
    "marketing": {
      "animations": [...],
      "budgetROI": {...}
    }
  }
}
```

---

## Testing

Use `visit_id = 123` for all dev testing. This is the default if not specified.

To test in Swagger: http://localhost:8000/docs

POST /visits/analyze with:
```json
{
  "visit_data": {...},
  "manager_id": 999,
  "delegate_id": 123,
  "zone_id": "Tunis Nord"
}
```

Response includes all 21 agents + cache metadata.

---

## Deployment Checklist

- [ ] All three apps' api.ts files updated (done ✓)
- [ ] Shared useOrchestrator hook created (done ✓)
- [ ] App-specific hooks created (done ✓)
- [ ] direction_web views updated to use useFounderData
- [ ] manager_web views updated to use useManagerData
- [ ] marketing_web views updated to use useMarketingData
- [ ] Delete mock data files (delegates.ts, animData.ts)
- [ ] Test all views with real API data
- [ ] Verify cache TTL (30 min) works
- [ ] Verify error handling (401/403 redirect to /login)
- [ ] Verify loading states show while fetching
- [ ] Production: Point web apps to external API endpoint
