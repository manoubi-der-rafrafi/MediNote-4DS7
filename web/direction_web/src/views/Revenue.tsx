import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { useQuery } from '@tanstack/react-query';
import { KpiCard } from '../components/KpiCard';
import { Pill } from '../components/Pill';
import { PrimeSimulator } from '../components/PrimeSimulator';
import api from '../lib/api';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function RevenueDashboard() {
  const visitId = 123;
  const { data: predictionResponse } = useQuery({
    queryKey: ['revenue', visitId],
    queryFn: () => api.get(`/predictions/${visitId}?role=founder`).then((r) => r.data),
  });

  const payload = predictionResponse?.data || predictionResponse || {};
  const totalCa = payload?.finance?.margins?.total_margin_dt || 0;
  const grossMargin = payload?.finance?.margins?.avg_margin_pct || 0;
  const arOutstanding = payload?.finance?.reliquat_aging?.total_outstanding || 0;
  const gratuityCost = payload?.finance?.gratuity_cost?.total_cost || 0;

  // KPIs
  const kpis = [
    {
      label: 'Total CA',
      value: `${(totalCa / 1000000).toFixed(1)}M`,
      delta: 0,
      barPercent: Math.min(100, Math.max(0, totalCa > 0 ? (totalCa / 1000000) : 0)),
      barColor: 'bg-ok',
    },
    {
      label: 'Gross margin',
      value: `${Number(grossMargin).toFixed(1)}%`,
      delta: 0,
      deltaType: 'down' as const,
      barPercent: Math.min(100, Math.max(0, Number(grossMargin))),
      barColor: 'bg-warn',
    },
    {
      label: 'AR outstanding',
      value: `${(arOutstanding / 1000000).toFixed(1)}M`,
      delta: 0,
      deltaType: 'warn' as const,
      barPercent: Math.min(100, Math.max(0, arOutstanding > 0 ? (arOutstanding / 1000000) : 0)),
      barColor: 'bg-warn',
    },
    {
      label: 'Gratuity cost',
      value: `${(gratuityCost / 1000000).toFixed(1)}M`,
      delta: 0,
      barPercent: Math.min(100, Math.max(0, gratuityCost > 0 ? (gratuityCost / 1000000) : 0)),
      barColor: 'bg-ok',
    },
  ];

  // Waterfall data
  const waterfallData = {
    labels: ['CA', 'COGS', 'Gratuités', 'AR provision', 'Prime', 'Net'],
    datasets: [{
      label: 'Amount (M DT)',
      data: [209, -132, -9.8, -4.2, -8.1, 54.9],
      backgroundColor: ['#1D9E75', '#BA7517', '#BA7517', '#BA7517', '#BA7517', '#1D9E75'],
      borderRadius: 4,
    }],
  };

  // AR Aging data
  const arAgingData = {
    labels: ['0-30d', '31-60d', '61-90d', '91-180d', '>180d'],
    datasets: [{
      label: 'M DT',
      data: [22.1, 8.4, 3.6, 8.9, 5.2],
      backgroundColor: ['#1D9E75', '#378ADD', '#BA7517', '#B8263E', '#6B1F1F'],
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
      <h1 className="text-3xl font-bold text-ink mb-1">Revenue & Finance</h1>
      <p className="text-mute text-sm mb-6">Analysis of margins, receivables, and gratuity costs</p>

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
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">Waterfall: CA to Net</h3>
          <div style={{ height: '260px' }}>
            <Bar data={waterfallData} options={chartOptions} />
          </div>
        </div>
        <div className="bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">AR aging</h3>
          <div style={{ height: '260px' }}>
            <Bar data={arAgingData} options={chartOptions} />
          </div>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-2 gap-4">
        {/* Articles Table */}
        <div className="bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">Top articles</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line">
                <th className="text-left py-2 text-xs font-semibold text-mute">Article</th>
                <th className="text-right py-2 text-xs font-semibold text-mute">CA (M DT)</th>
                <th className="text-right py-2 text-xs font-semibold text-mute">Margin %</th>
                <th className="text-right py-2 text-xs font-semibold text-mute">Gratuité %</th>
                <th className="text-right py-2 text-xs font-semibold text-mute">Net</th>
              </tr>
            </thead>
            <tbody>
              {[
                { code: 'ART001', ca: 28.5, margin: 38, gratuity: 8.2 },
                { code: 'ART002', ca: 24.2, margin: 35, gratuity: 12.1 },
                { code: 'ART003', ca: 21.8, margin: 28, gratuity: 18.5 },
                { code: 'ART004', ca: 19.5, margin: 32, gratuity: 15.3 },
                { code: 'ART005', ca: 18.3, margin: 26, gratuity: 22.0 },
                { code: 'ART006', ca: 17.2, margin: 34, gratuity: 9.1 },
              ].map((row) => (
                <tr key={row.code} className="border-b border-line/50 hover:bg-gray-50">
                  <td className="py-2 font-mono text-xs">{row.code}</td>
                  <td className="text-right py-2 font-medium">{row.ca}M</td>
                  <td className="text-right py-2">{row.margin}%</td>
                  <td className="text-right py-2 text-warn">{row.gratuity}%</td>
                  <td className="text-right py-2">
                    <Pill variant="ok" text={((row.ca * row.margin / 100) * (1 - row.gratuity / 100)).toFixed(1)} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Prime Simulator */}
        <PrimeSimulator />
      </div>
    </div>
  );
}
