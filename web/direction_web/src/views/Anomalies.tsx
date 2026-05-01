import { Chart as ChartJS, CategoryScale, LinearScale, LineElement, PointElement, BarElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import { KpiCard } from '../components/KpiCard';
import { Pill } from '../components/Pill';

ChartJS.register(CategoryScale, LinearScale, LineElement, PointElement, BarElement, Title, Tooltip, Legend, Filler);

export default function AnomaliesDashboard() {
  const kpis = [
    { label: 'Flagged reports', value: '123', delta: 8, deltaType: 'warn' as const, barPercent: 8, barColor: 'bg-bad' },
    { label: 'Delegates flagged', value: '12/143', delta: -8.4, barPercent: 8.4, barColor: 'bg-warn' },
    { label: 'Contradiction rate', value: '3.1%', delta: 0.8, deltaType: 'down' as const, barPercent: 3.1, barColor: 'bg-warn' },
    { label: 'Avg anomaly score', value: '0.18', delta: -5, barPercent: 18, barColor: 'bg-ok' },
  ];

  // Anomaly rate over time
  const anomalyRateData = {
    labels: ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8', 'W9', 'W10', 'W11', 'W12'],
    datasets: [{
      label: 'Anomaly rate %',
      data: [6.2, 5.8, 7.1, 6.9, 8.4, 7.8, 8.9, 8.2, 9.1, 8.7, 8.3, 8.0],
      borderColor: '#B8263E',
      backgroundColor: 'rgba(184, 38, 62, 0.1)',
      fill: true,
      tension: 0.3,
    }],
  };

  // Flag type distribution
  const flagTypeData = {
    labels: ['Contradic.', 'Inflated+', 'Sparse', 'Duplicate', 'No follow', 'Off-zone'],
    datasets: [{
      label: 'Count',
      data: [38, 29, 22, 18, 12, 4],
      backgroundColor: '#BA7517',
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
      <h1 className="text-3xl font-bold text-ink mb-1">Anomalies & Alerts</h1>
      <p className="text-mute text-sm mb-6">Data quality issues and flagged transactions</p>

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
          <h3 className="text-lg font-semibold text-ink mb-4">Anomaly rate over time</h3>
          <div style={{ height: '260px' }}>
            <Line data={anomalyRateData} options={chartOptions} />
          </div>
        </div>
        <div className="bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">Flag type distribution</h3>
          <div style={{ height: '260px' }}>
            <Bar data={flagTypeData} options={chartOptions} />
          </div>
        </div>
      </div>

      {/* Recent Anomalies Table */}
      <div className="bg-card border border-line rounded-lg p-5">
        <h3 className="text-lg font-semibold text-ink mb-4">Recent anomalies</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line">
              <th className="text-left py-2 text-xs font-semibold text-mute">Date</th>
              <th className="text-left py-2 text-xs font-semibold text-mute">Delegate</th>
              <th className="text-left py-2 text-xs font-semibold text-mute">Pharmacy</th>
              <th className="text-center py-2 text-xs font-semibold text-mute">Flags</th>
              <th className="text-right py-2 text-xs font-semibold text-mute">Score</th>
              <th className="text-left py-2 text-xs font-semibold text-mute">Reason</th>
            </tr>
          </thead>
          <tbody>
            {[
              { date: '2026-04-18', delegate: 'Mohamed K.', pharmacy: 'Pharma Tunis', flags: 2, score: 0.82, reason: 'Inflated qty + off-zone' },
              { date: '2026-04-17', delegate: 'Leila M.', pharmacy: 'Pharma Sfax', flags: 1, score: 0.56, reason: 'Duplicate visit' },
              { date: '2026-04-17', delegate: 'Ahmed B.', pharmacy: 'Pharma Ariana', flags: 3, score: 0.91, reason: 'Contradiction + gratuité + sparse' },
              { date: '2026-04-16', delegate: 'Youssef M.', pharmacy: 'Pharma Ben Arous', flags: 1, score: 0.48, reason: 'No follow-up 45d' },
              { date: '2026-04-16', delegate: 'Fatima E.', pharmacy: 'Pharma Sousse', flags: 2, score: 0.71, reason: 'Zero sales + overstock' },
            ].map((row, idx) => (
              <tr key={idx} className="border-b border-line/50 hover:bg-gray-50">
                <td className="py-2 text-xs text-mute">{row.date}</td>
                <td className="py-2 font-medium">{row.delegate}</td>
                <td className="py-2 text-xs">{row.pharmacy}</td>
                <td className="text-center py-2">
                  <Pill variant="warn" text={`${row.flags}`} />
                </td>
                <td className="text-right py-2 font-semibold">{row.score.toFixed(2)}</td>
                <td className="py-2 text-xs text-mute">{row.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
