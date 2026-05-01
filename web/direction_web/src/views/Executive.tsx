import { useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import { KpiCard } from '../components/KpiCard';
import { AlertBadge } from '../components/AlertBadge';
import { useFounderData } from '../hooks/useFounderData';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const chartDefaults = {
  font: { family: '-apple-system, BlinkMacSystemFont, "SF Pro Display", Inter, system-ui, sans-serif', size: 11 },
  color: '#6B6B66',
};

ChartJS.defaults.font = { ...chartDefaults.font };
ChartJS.defaults.color = chartDefaults.color;

type Period = 'MTD' | 'QTD' | 'YTD';

export default function ExecutiveDashboard() {
  const [period, setPeriod] = useState<Period>('QTD');
  const { kpis, revenue, market, anomalies, forecasts, loading, error, refetch, executionTime, fromCache } = useFounderData(123);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-12 h-12 border-4 border-gray-200 border-t-blue-500 rounded-full animate-spin" />
      </div>
    );
  }
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <h3 className="text-red-800 font-semibold">Error Loading Data</h3>
        <p className="text-red-700 text-sm mt-1">{(error as Error)?.message || 'An unexpected error occurred'}</p>
        <button
          onClick={refetch}
          className="mt-3 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700 transition"
        >
          Try Again
        </button>
      </div>
    );
  }

  // Transform API data to component props
  const formatKPIs = () => {
    if (!kpis || typeof kpis !== 'object' || Object.keys(kpis).length === 0) {
      return [
        { label: 'Total CA', value: '—', delta: 0, barPercent: 0, barColor: 'bg-ok' },
        { label: 'Channel imbalance', value: '—', delta: 0, deltaType: 'warn' as const, barPercent: 0, barColor: 'bg-warn' },
        { label: 'Prime realization', value: '—', delta: 0, deltaType: 'down' as const, barPercent: 0, barColor: 'bg-bad' },
        { label: 'Budget execution', value: '—', delta: 0, deltaType: 'down' as const, barPercent: 0, barColor: 'bg-bad' },
      ];
    }

    return [
      {
        label: 'Total CA',
        value: kpis.total_ca ? `${(kpis.total_ca / 1e6).toFixed(0)}M DT` : '—',
        delta: kpis.ca_delta_pct || 0,
        barPercent: Math.min(100, (kpis.total_ca || 0) / (kpis.target_ca || 1) * 100),
        barColor: 'bg-ok',
      },
      {
        label: 'Channel imbalance',
        value: kpis.channel_ratio ? `${kpis.channel_ratio}%` : '—',
        delta: kpis.channel_delta_pct || 0,
        deltaType: 'warn' as const,
        barPercent: kpis.channel_ratio || 0,
        barColor: 'bg-warn',
      },
      {
        label: 'Prime realization',
        value: kpis.prime_realization_pct ? `${kpis.prime_realization_pct.toFixed(1)}%` : '—',
        delta: (kpis.prime_realization_pct || 0) - 100,
        deltaType: 'down' as const,
        barPercent: kpis.prime_realization_pct || 0,
        barColor: 'bg-bad',
      },
      {
        label: 'Budget execution',
        value: kpis.budget_execution_pct ? `${kpis.budget_execution_pct.toFixed(1)}%` : '—',
        delta: (kpis.budget_execution_pct || 0) - 100,
        deltaType: 'down' as const,
        barPercent: kpis.budget_execution_pct || 0,
        barColor: 'bg-bad',
      },
    ];
  };

  // Revenue trend data from API or fallback
  const revenueTrendData = revenue?.trend_data || {
    labels: ['2019', '2020', '2021', '2022', '2023', '2024', '2025E', '2026E'],
    datasets: [
      {
        label: 'Grossiste',
        data: [124, 132, 141, 152, 165, 174, 181, 176],
        borderColor: '#7F77DD',
        backgroundColor: 'rgba(127, 119, 221, 0.1)',
        fill: true,
        tension: 0.3,
      },
      {
        label: 'Pharma direct',
        data: [14, 16, 18, 21, 23, 25, 27, 27],
        borderColor: '#1D9E75',
        backgroundColor: 'rgba(29, 158, 117, 0.1)',
        fill: true,
        tension: 0.3,
      },
      {
        label: 'Total',
        data: [142, 152, 163, 177, 192, 203, 211, 209],
        borderColor: '#1F1F1D',
        borderDash: [5, 5],
        fill: false,
        tension: 0.3,
        pointRadius: 0,
      },
    ],
  };

  // Transform anomalies for alert badges
  const getAlertBadges = () => {
    if (!anomalies || !Array.isArray(anomalies)) {
      return [
        <AlertBadge key="1" type="info" title="Data" message="Loading anomalies..." />,
      ];
    }

    return anomalies.slice(0, 5).map((anom: any, idx: number) => (
      <AlertBadge
        key={idx}
        type={anom.severity === 'critical' ? 'bad' : anom.severity === 'warning' ? 'warn' : 'info'}
        title={anom.title || `Alert ${idx + 1}`}
        message={anom.message || 'See details'}
      />
    ));
  };

  const revenueOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom' as const, labels: { boxWidth: 10 } },
    },
    scales: {
      y: { beginAtZero: true, grid: { drawTicks: false } },
      x: { grid: { display: false } },
    },
  };

  const concentrationData = {
    labels: ['Top5', 'Next20', 'Next100', 'LongTail'],
    datasets: [{
      data: market?.concentration_pct
        ? [
            market.concentration_pct.top5 ?? 22,
            market.concentration_pct.next20 ?? 28,
            market.concentration_pct.next100 ?? 31,
            market.concentration_pct.long_tail ?? 19,
          ]
        : [22, 28, 31, 19],
      backgroundColor: ['#B8263E', '#BA7517', '#378ADD', '#D3D1C7'],
    }],
  };

  const zones = Array.isArray(market?.top_zones) && market.top_zones.length > 0
    ? market.top_zones.slice(0, 10)
    : null;
  const topZonesData = {
    labels: zones
      ? zones.map((z: any) => z.zone || z.gouvernorat || z.name)
      : ['Tunis N', 'Sfax S', 'Sousse', 'Nabeul', 'Bizerte', 'Ariana', 'Kairouan', 'Monastir', 'Mahdia', 'Ben Arous'],
    datasets: [{
      label: 'Articles',
      data: zones
        ? zones.map((z: any) => z.articles || z.count || z.value)
        : [32, 28, 24, 21, 18, 17, 15, 14, 13, 12],
      backgroundColor: '#378ADD',
      borderRadius: 4,
    }],
  };

  const zoneOptions = {
    indexAxis: 'y' as const,
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: { x: { grid: { drawTicks: false } }, y: { grid: { display: false } } },
  };

  const kpiData = formatKPIs();

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-ink mb-1">Executive Dashboard</h1>
          <p className="text-mute text-sm">
            {kpis?.total_ca ? `${(kpis.total_ca / 1e6).toFixed(0)}M DT CA · ` : ''}
            Updated {new Date().toLocaleDateString('fr-FR')}
            {fromCache && ' · (cached)'}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-mute">Exec time: {executionTime?.toFixed(2)}s</p>
          <button
            onClick={refetch}
            className="text-xs text-info hover:underline mt-1"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Period toggle */}
      <div className="flex gap-2 mb-6">
        {(['MTD', 'QTD', 'YTD'] as Period[]).map((p) => (
          <button
            key={p}
            onClick={() => setPeriod(p)}
            className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
              period === p ? 'bg-info text-white' : 'bg-line text-ink hover:bg-line/80'
            }`}
          >
            {p}
          </button>
        ))}
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {kpiData.map((kpi, idx) => (
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

      {/* Revenue Trend + Alerts */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="col-span-2 bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">Revenue trend 2019→2026 <span className="text-xs text-mute ml-2">{period}</span></h3>
          <div style={{ height: '260px' }}>
            <Line data={revenueTrendData} options={revenueOptions} />
          </div>
        </div>
        <div className="bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">Strategic risk alerts</h3>
          {getAlertBadges()}
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {/* Top Zones */}
        <div className="bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">Top 10 zones <span className="text-xs text-mute ml-2">{period}</span></h3>
          <div style={{ height: '260px' }}>
            <Bar data={topZonesData} options={zoneOptions} />
          </div>
        </div>

        {/* Concentration */}
        <div className="bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">Article concentration <span className="text-xs text-mute ml-2">{period}</span></h3>
          <div style={{ height: '260px' }}>
            <Doughnut data={concentrationData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' as const } } }} />
          </div>
        </div>

        {/* Forecast card */}
        <div className="bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">6-month forecast</h3>
          <div className="space-y-3 text-sm">
            <div>
              <div className="text-mute text-xs">Q2 revenue</div>
              <div className="text-xl font-bold text-ink">{forecasts?.q2_revenue || '—'} <span className="text-mute text-xs">±{forecasts?.confidence_interval || '—'}%</span></div>
            </div>
            <div>
              <div className="text-mute text-xs">Expiry loss</div>
              <div className="text-xl font-bold text-bad">{forecasts?.expiry_loss || '—'}</div>
            </div>
            <div>
              <div className="text-mute text-xs">Delegates at risk</div>
              <div className="text-xl font-bold text-warn">{forecasts?.delegates_at_risk || '—'}</div>
            </div>
            <div>
              <div className="text-mute text-xs">White-spots</div>
              <div className="text-xl font-bold text-ink">{forecasts?.white_spots || '—'}</div>
            </div>
            <div>
              <div className="text-mute text-xs">Reorder opt</div>
              <div className="text-xl font-bold text-ok">{forecasts?.reorder_optimization || '—'}</div>
            </div>
            <div>
              <div className="text-mute text-xs">Anim AUC</div>
              <div className="text-xl font-bold text-ok">{forecasts?.animation_auc || '—'}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
