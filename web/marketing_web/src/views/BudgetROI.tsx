import React from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, LineElement, BarElement, PointElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import { KpiCard } from '../components/KpiCard';
import { useMarketingData } from '../hooks/useMarketingData';

ChartJS.register(CategoryScale, LinearScale, LineElement, BarElement, PointElement, Title, Tooltip, Legend, Filler);

export const BudgetROI: React.FC = () => {
  const { budgetROI, roiAnalysis, loading } = useMarketingData(123);

  const budget = budgetROI as any;
  const roi    = roiAnalysis as any;

  // KPIs — real API data with static fallbacks
  const totalRequested = budget?.total_budget != null
    ? `${(budget.total_budget / 1_000_000).toFixed(1)}M DT`
    : '5.1M DT';
  const totalInvested  = budget?.total_revenue != null
    ? `${(budget.total_revenue / 1_000_000).toFixed(1)}M DT`
    : '1.8M DT';
  const unusedBudget   = budget?.total_budget != null && budget?.total_revenue != null
    ? `${((budget.total_budget - budget.total_revenue) / 1_000_000).toFixed(1)}M DT`
    : '3.3M DT';
  const execPct        = budget?.total_budget && budget?.total_revenue
    ? +((budget.total_revenue / budget.total_budget) * 100).toFixed(1)
    : 35.3;
  const avgROI         = roi?.avg_roi_ratio != null
    ? `${roi.avg_roi_ratio.toFixed(1)}×`
    : '2.1×';

  const kpis = [
    { label: 'Total requested', value: totalRequested, delta: 0,     barPercent: 100,    barColor: 'bg-brand' },
    { label: 'Actually invested', value: totalInvested, delta: -64.7, deltaType: 'down' as const, barPercent: execPct,  barColor: 'bg-bad' },
    { label: 'Unused budget',   value: unusedBudget,   delta: 65,    deltaType: 'warn' as const, barPercent: 100 - execPct, barColor: 'bg-warn' },
    { label: 'Avg ROI',         value: avgROI,         delta: 8,     barPercent: Math.min(100, (roi?.avg_roi_ratio ?? 2.1) * 25), barColor: 'bg-ok' },
  ];

  // ROI ranking — all animations from API or fallback
  const allAnims = roi?.top_performers;
  const roiRankLabels = Array.isArray(allAnims) && allAnims.length > 0
    ? allAnims.map((a: any) => a.name || `Anim ${a.animation_id}`)
    : Array.from({ length: 20 }, (_, i) => `Anim ${i + 1}`);
  const roiRankValues = Array.isArray(allAnims) && allAnims.length > 0
    ? allAnims.map((a: any) => +(a.roi_ratio ?? a.composite_score ?? 0).toFixed(2))
    : [4.2, 3.6, 2.8, 2.1, 1.8, 1.4, 0.6, 0.3, 2.5, 2.2, 1.9, 1.6, 1.3, 1.0, 0.7, 0.4, 2.0, 1.5, 0.9, 0.5];

  const quarterlyData = {
    labels: ['Q1\'25', 'Q2\'25', 'Q3\'25', 'Q4\'25', 'Q1\'26'],
    datasets: [
      { label: 'Requested', data: [1.2, 1.3, 1.4, 1.5, 1.3], borderColor: '#F4C0D1', backgroundColor: 'rgba(244, 192, 209, 0.1)', fill: true, tension: 0.3 },
      { label: 'Invested',  data: [0.48, 0.52, 0.61, 0.58, 0.46], borderColor: '#D4537E', backgroundColor: 'rgba(212, 83, 126, 0.1)', fill: true, tension: 0.3 },
    ],
  };

  const budgetByTypeData = {
    labels: ['Training', 'Event', 'PLV', 'Digital', 'Promo', 'Contest'],
    datasets: [
      { label: 'Requested', data: [180, 240, 95, 65, 290, 120], backgroundColor: '#F4C0D1', borderRadius: 4 },
      { label: 'Invested',  data: [165, 172, 78, 29, 164,  24], backgroundColor: '#D4537E', borderRadius: 4 },
    ],
  };

  const roiRankingData = {
    labels: roiRankLabels,
    datasets: [{
      label: 'ROI',
      data: roiRankValues,
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

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: 'bottom' as const } },
    scales: { x: { grid: { display: false } }, y: { grid: { drawTicks: false } } },
  };

  return (
    <div>
      <h1 className="text-3xl font-bold text-ink mb-1">Budget & ROI</h1>
      <p className="text-mute text-sm mb-6">
        Financial analysis and performance metrics{loading ? ' · Loading…' : ''}
      </p>

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

      {/* Charts */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">Quarterly budget trend</h3>
          <div style={{ height: '260px' }}>
            <Line data={quarterlyData} options={chartOptions} />
          </div>
        </div>
        <div className="bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">Budget by type — req vs inv</h3>
          <div style={{ height: '260px' }}>
            <Bar data={budgetByTypeData} options={chartOptions} />
          </div>
        </div>
      </div>

      {/* ROI Ranking */}
      <div className="bg-card border border-line rounded-lg p-5">
        <h3 className="text-lg font-semibold text-ink mb-4">
          ROI ranking — all {roiRankLabels.length}
        </h3>
        <div style={{ height: '260px' }}>
          <Bar data={roiRankingData} options={chartOptions} />
        </div>
      </div>
    </div>
  );
};
