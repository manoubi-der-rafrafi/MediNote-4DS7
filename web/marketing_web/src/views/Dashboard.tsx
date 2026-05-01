import React from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';
import { KpiCard } from '../components/KpiCard';
import { HeroBanner } from '../components/HeroBanner';
import { RecoCard } from '../components/RecoCard';
import { ThemeTag } from '../components/ThemeTag';
import { useMarketingData } from '../hooks/useMarketingData';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend);

export const Dashboard: React.FC = () => {
  const [period, setPeriod] = React.useState<'MTD'|'QTD'|'YTD'>('QTD');
  const { roiAnalysis, themes, sentimentAnalysis, budgetROI, animations, loading } = useMarketingData(123);

  const roi    = roiAnalysis as any;
  const sent   = sentimentAnalysis as any;
  const budget = budgetROI as any;

  // KPIs — real API data with static fallbacks
  const totalAnimations = roi?.total_animations ?? 32;
  const budgetExecPct   = budget?.total_budget && budget?.total_revenue
    ? +((budget.total_revenue / budget.total_budget) * 100).toFixed(1)
    : 35.3;
  const mouvFortPct     = roi?.avg_mouvement_fort_pct != null
    ? +(roi.avg_mouvement_fort_pct * 100).toFixed(1)
    : 46.2;
  const sentimentPosPct = sent?.positive_pct != null ? +(sent.positive_pct).toFixed(0) : 68;

  const kpis = [
    { label: 'Animations',   value: String(totalAnimations), delta: 0,     barPercent: 100,             barColor: 'bg-brand' },
    { label: 'Budget exec',  value: `${budgetExecPct}%`,     delta: -64.7, deltaType: 'down' as const,  barPercent: budgetExecPct,    barColor: 'bg-bad' },
    { label: 'Mouv. fort %', value: `${mouvFortPct}%`,       delta: 15.2,  barPercent: mouvFortPct,     barColor: 'bg-ok' },
    { label: 'Sentiment +',  value: `${sentimentPosPct}%`,   delta: 4,     barPercent: sentimentPosPct, barColor: 'bg-ok' },
  ];

  // ROI bar chart — top animations from API or fallback labels
  const apiAnims  = Array.isArray(animations) && animations.length > 0 ? animations : null;
  const roiLabels = apiAnims
    ? apiAnims.slice(0, 8).map((a: any) => a.name || a.animation_name || `Anim ${a.animation_id}`)
    : ['Form.γ-3', 'Cardio', 'Kit vitrine', 'Ramadan', 'Webinaire X', 'Gratuités', 'Salon Sud', 'Concours C'];
  const roiValues = apiAnims
    ? apiAnims.slice(0, 8).map((a: any) => +(a.roi_ratio ?? a.composite_score ?? 0).toFixed(2))
    : [4.2, 3.6, 2.8, 2.1, 1.8, 1.4, 0.6, 0.3];

  const roiData = {
    labels: roiLabels,
    datasets: [{
      label: 'ROI',
      data: roiValues,
      backgroundColor: (ctx: any) => {
        const v = ctx.parsed.y;
        if (v >= 2.5) return '#1D9E75';
        if (v >= 1.5) return '#378ADD';
        if (v >= 1)   return '#BA7517';
        return '#B8263E';
      },
      borderRadius: 4,
    }],
  };

  // Sentiment doughnut — from NLP quality distribution
  const sentDist = sent?.distribution;
  const sentimentData = {
    labels: ['Positive', 'Neutral', 'Negative'],
    datasets: [{
      data: sentDist
        ? [
            sentDist.A_excellent_pct ?? 68,
            ((sentDist.B_good_pct ?? 0) + (sentDist.C_acceptable_pct ?? 0)) || 22,
            sentDist.D_poor_pct ?? 10,
          ]
        : [68, 22, 10],
      backgroundColor: ['#1D9E75', '#D3D1C7', '#B8263E'],
    }],
  };

  const budgetByTypeData = {
    labels: ['Training', 'Event', 'PLV', 'Digital', 'Promo', 'Contest'],
    datasets: [
      { label: 'Requested', data: [180, 240, 95, 65, 290, 120], backgroundColor: '#F4C0D1', borderRadius: 4 },
      { label: 'Invested',  data: [165, 172, 78, 29, 164,  24], backgroundColor: '#D4537E', borderRadius: 4 },
    ],
  };

  // Themes — API or fallback
  const apiThemes = Array.isArray(themes) && themes.length > 0 ? themes : null;
  const themeList = apiThemes || [
    { label: 'stock', count: 312 }, { label: 'conseil', count: 287 },
    { label: 'concurrence', count: 241 }, { label: 'emplacement', count: 198 },
    { label: 'formation', count: 176 }, { label: 'prix', count: 154 },
    { label: 'rupture', count: 132 }, { label: 'eff.indésirable', count: 44 },
  ];

  // Top/bottom recos from API
  const topAnims  = apiAnims ? apiAnims.slice(0, 2) : null;
  const dropAnims = apiAnims ? [...apiAnims].reverse().slice(0, 2) : null;

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: 'bottom' as const } },
    scales: { x: { grid: { display: false } }, y: { grid: { drawTicks: false } } },
  };

  return (
    <div>
      <div className="flex justify-between items-baseline mb-4">
        <h1 className="text-3xl font-bold text-ink">Marketing Dashboard</h1>
        <span className="text-sm text-mute">
          {totalAnimations} animations · 1,541 visit reports · 79 zones
          {loading ? ' · Loading…' : ''}
        </span>
      </div>

      <div className="flex gap-3 mb-6">
        {['MTD', 'QTD', 'YTD'].map((p) => (
          <button
            key={p}
            onClick={() => setPeriod(p as 'MTD'|'QTD'|'YTD')}
            className={`px-3 py-1 text-xs font-semibold rounded border ${
              period === p
                ? 'bg-brand text-white border-brand'
                : 'bg-transparent text-ink border-line hover:border-brand'
            }`}
          >
            {p}
          </button>
        ))}
      </div>

      <HeroBanner
        label="Prediction model"
        value={`AUC = ${roi?.predictions?.model_auc?.toFixed(2) ?? '1.00'}`}
        description="P(mouvement fort) — perfect separation on holdout. Score any animation before budget commit."
      />

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {kpis.map((kpi, idx) => (
          <KpiCard
            key={idx}
            label={kpi.label}
            value={kpi.value}
            delta={kpi.delta}
            deltaType={kpi.deltaType || 'up'}
            barPercent={kpi.barPercent}
            barColor={kpi.barColor}
          />
        ))}
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="col-span-2 bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">Animation ROI — top 8 <span className="text-xs text-mute ml-2">{period}</span></h3>
          <div style={{ height: '260px' }}>
            <Bar data={roiData} options={chartOptions} />
          </div>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-ink">Next-cycle recos</h3>
          {topAnims
            ? topAnims.map((a: any) => (
                <RecoCard key={a.animation_id} type="keep"
                  title={a.name || `Anim ${a.animation_id}`}
                  subtitle={`ROI ${(a.roi_ratio ?? 0).toFixed(1)}×`}
                />
              ))
            : <>
                <RecoCard type="keep" title="Formation γ-3"  subtitle="ROI 4.2×, P=0.94" />
                <RecoCard type="keep" title="Journée cardio" subtitle="mouv.fort 71%" />
              </>
          }
          <RecoCard type="watch" title="Webinaire X" subtitle="slow burn" />
          {dropAnims
            ? dropAnims.map((a: any) => (
                <RecoCard key={a.animation_id} type="drop"
                  title={a.name || `Anim ${a.animation_id}`}
                  subtitle={`ROI ${(a.roi_ratio ?? 0).toFixed(1)}×`}
                />
              ))
            : <>
                <RecoCard type="drop" title="Salon Sud"  subtitle="ROI 0.6×" />
                <RecoCard type="drop" title="Concours C" subtitle="0 conversion" />
              </>
          }
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">Sentiment breakdown <span className="text-xs text-mute ml-2">{period}</span></h3>
          <div style={{ height: '260px' }}>
            <Doughnut data={sentimentData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' as const } } }} />
          </div>
        </div>

        <div className="col-span-2 bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">Budget req vs invested by type <span className="text-xs text-mute ml-2">{period}</span></h3>
          <div style={{ height: '260px' }}>
            <Bar data={budgetByTypeData} options={chartOptions} />
          </div>
        </div>
      </div>

      {/* Top Themes */}
      <div className="bg-card border border-line rounded-lg p-5">
        <h3 className="text-lg font-semibold text-ink mb-4">Top themes</h3>
        <div className="mb-4">
          {themeList.map((t: any) => (
            <ThemeTag key={t.label} label={t.label} count={t.count} />
          ))}
        </div>
        <p className="text-sm text-bad font-semibold">Concurrence up +28% vs Q4 '25</p>
      </div>
    </div>
  );
};
