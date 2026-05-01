import React from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { KpiCard } from '../components/KpiCard';
import { Pill } from '../components/Pill';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export const Forecasts: React.FC = () => {
  const kpis = [
    { label: 'Model AUC', value: '1.00', delta: 0, barPercent: 100, barColor: 'bg-ok' },
    { label: 'Burn rate Q2', value: '42%', delta: 6.7, barPercent: 42, barColor: 'bg-ok' },
    { label: 'Penetration gap', value: '14 gov.', delta: -12, deltaType: 'warn' as const, barPercent: 58, barColor: 'bg-warn' },
    { label: 'Expected ROI Q2', value: '2.6×', delta: 0.5, barPercent: 65, barColor: 'bg-ok' },
  ];

  const burnRateData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'],
    datasets: [
      {
        label: 'Actual',
        data: [142, 128, 168, 180, null, null, null, null, null],
        borderColor: '#D4537E',
        backgroundColor: 'rgba(212, 83, 126, 0.3)',
        fill: true,
        tension: 0.3,
      },
      {
        label: 'Forecast',
        data: [null, null, null, null, 195, 210, 225, 240, 255],
        borderColor: '#F4C0D1',
        borderDash: [5, 5],
        fill: false,
        tension: 0.3,
      },
    ],
  };

  const penetrationData = {
    labels: ['Tunis', 'Sfax', 'Sousse', 'Nabeul', 'Bizerte', 'Ariana', 'Kairouan', 'Gabès', 'Médenine', 'Kasserine', 'Tataouine', 'Gafsa', 'Kef', 'Zaghouan'],
    datasets: [{
      label: '% Coverage',
      data: [92, 86, 82, 74, 68, 84, 58, 54, 48, 34, 31, 42, 32, 41],
      backgroundColor: (ctx: any) => {
        const value = ctx.parsed.y;
        if (value >= 75) return '#1D9E75';
        if (value >= 55) return '#378ADD';
        if (value >= 40) return '#BA7517';
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
      <h1 className="text-3xl font-bold text-ink mb-1">Forecasts</h1>
      <p className="text-mute text-sm mb-6">ML predictions for next-cycle animations</p>

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
          <h3 className="text-lg font-semibold text-ink mb-4">Budget burn forecast</h3>
          <div style={{ height: '260px' }}>
            <Bar data={burnRateData} options={chartOptions} />
          </div>
        </div>
        <div className="bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">Market penetration by gov.</h3>
          <div style={{ height: '260px' }}>
            <Bar data={penetrationData} options={{ ...chartOptions, indexAxis: 'y' as const }} />
          </div>
        </div>
      </div>

      {/* Predictions Table */}
      <div className="bg-card border border-line rounded-lg p-5">
        <h3 className="text-lg font-semibold text-ink mb-4">Predicted next-cycle winners</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line">
              <th className="text-left py-2 text-xs font-semibold text-mute">Animation</th>
              <th className="text-left py-2 text-xs font-semibold text-mute">Type</th>
              <th className="text-right py-2 text-xs font-semibold text-mute">Budget</th>
              <th className="text-right py-2 text-xs font-semibold text-mute">P(strong)</th>
              <th className="text-right py-2 text-xs font-semibold text-mute">Expected ROI</th>
              <th className="text-center py-2 text-xs font-semibold text-mute">Action</th>
            </tr>
          </thead>
          <tbody>
            {[
              { name: 'Formation γ-4 (nouveau)', type: 'Training', budget: '135K', p: 0.96, roi: '4.5×', action: 'ok' },
              { name: 'Journée pédiatrie', type: 'Event', budget: '98K', p: 0.91, roi: '3.8×', action: 'ok' },
              { name: 'Kit vitrine Q3', type: 'PLV', budget: '52K', p: 0.84, roi: '2.9×', action: 'ok' },
              { name: 'Webinaire Y', type: 'Digital', budget: '28K', p: 0.71, roi: '1.9×', action: 'info' },
              { name: 'Concours B (repeat)', type: 'Contest', budget: '65K', p: 0.62, roi: '1.5×', action: 'warn' },
            ].map((row, idx) => (
              <tr key={idx} className="border-b border-line/50 hover:bg-gray-50">
                <td className="py-2 font-medium">{row.name}</td>
                <td className="py-2 text-xs">{row.type}</td>
                <td className="text-right py-2 font-semibold">{row.budget}</td>
                <td className="text-right py-2 font-semibold">{row.p}</td>
                <td className="text-right py-2 font-semibold">{row.roi}</td>
                <td className="text-center py-2">
                  <Pill variant={row.action as any} text={row.action === 'ok' ? 'Launch' : row.action === 'info' ? 'Trial' : 'Reduce'} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
