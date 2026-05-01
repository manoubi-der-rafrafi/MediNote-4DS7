import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';
import { KpiCard } from '../components/KpiCard';
import { Pill } from '../components/Pill';

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend, Filler);

export default function DataQualityDashboard() {
  const kpis = [
    { label: 'Tables', value: '122', delta: 0, barPercent: 100, barColor: 'bg-info' },
    { label: 'Empty tables', value: '24', delta: -2, deltaType: 'warn' as const, barPercent: 19.7, barColor: 'bg-warn' },
    { label: 'Schema violations', value: '7', delta: -1, barPercent: 5.7, barColor: 'bg-warn' },
    { label: 'Drift alerts', value: '3', delta: 1, deltaType: 'down' as const, barPercent: 2.5, barColor: 'bg-ok' },
  ];

  // Completeness by domain
  const completenessData = {
    labels: ['Finance', 'Orders', 'People', 'Animations', 'Market', 'Ops', 'QA'],
    datasets: [{
      label: 'Completeness %',
      data: [98, 96, 91, 82, 88, 94, 71],
      backgroundColor: (ctx: any) => {
        const value = ctx.parsed.y;
        if (value >= 95) return '#1D9E75';
        if (value >= 85) return '#378ADD';
        if (value >= 75) return '#BA7517';
        return '#B8263E';
      },
      borderRadius: 4,
    }],
  };

  // Drift detection 30d (multi-line)
  const driftData = {
    labels: ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'D11', 'D12', 'D13', 'D14', 'D15', 'D16', 'D17', 'D18', 'D19', 'D20', 'D21', 'D22', 'D23', 'D24', 'D25', 'D26', 'D27', 'D28', 'D29', 'D30'],
    datasets: [
      {
        label: 'Order amount (M DT)',
        data: [6.2, 6.5, 6.3, 6.8, 7.1, 6.9, 7.2, 7.5, 7.3, 7.6, 7.8, 8.1, 8.0, 8.3, 8.5, 8.2, 8.4, 8.6, 8.8, 8.5, 8.7, 8.9, 9.1, 8.8, 9.0, 9.2, 9.1, 9.3, 9.5, 9.2],
        borderColor: '#378ADD',
        tension: 0.3,
      },
      {
        label: 'Visit duration (mins)',
        data: [45, 46, 44, 47, 48, 46, 49, 50, 48, 51, 52, 50, 53, 51, 54, 52, 55, 53, 56, 52, 54, 52, 50, 48, 45, 42, 40, 38, 36, 35],
        borderColor: '#B8263E',
        tension: 0.3,
      },
      {
        label: 'Gratuity rate %',
        data: [15.2, 15.3, 15.4, 15.3, 15.5, 15.6, 15.7, 15.7, 15.8, 15.8, 15.9, 15.9, 16.0, 16.0, 15.9, 15.9, 15.8, 15.8, 15.7, 15.7, 15.7, 15.7, 15.7, 15.7, 15.7, 15.7, 15.7, 15.7, 15.7, 15.7],
        borderColor: '#1D9E75',
        tension: 0.3,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: 'bottom' as const } },
    scales: { x: { grid: { display: false } }, y: { grid: { drawTicks: false } } },
  };

  return (
    <div>
      <h1 className="text-3xl font-bold text-ink mb-1">Data Quality & IT</h1>
      <p className="text-mute text-sm mb-6">Schema completeness and drift detection</p>

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
          <h3 className="text-lg font-semibold text-ink mb-4">Completeness score per domain</h3>
          <div style={{ height: '260px' }}>
            <Bar data={completenessData} options={chartOptions} />
          </div>
        </div>
        <div className="bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">Drift detection (30d)</h3>
          <div style={{ height: '260px' }}>
            <Line data={driftData} options={chartOptions} />
          </div>
        </div>
      </div>

      {/* Data Tables Status */}
      <div className="bg-card border border-line rounded-lg p-5">
        <h3 className="text-lg font-semibold text-ink mb-4">Empty/sparse tables</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line">
              <th className="text-left py-2 text-xs font-semibold text-mute">Domain</th>
              <th className="text-right py-2 text-xs font-semibold text-mute">Expected rows</th>
              <th className="text-right py-2 text-xs font-semibold text-mute">Actual</th>
              <th className="text-right py-2 text-xs font-semibold text-mute">% Complete</th>
              <th className="text-left py-2 text-xs font-semibold text-mute">Last migration</th>
              <th className="text-center py-2 text-xs font-semibold text-mute">Status</th>
            </tr>
          </thead>
          <tbody>
            {[
              { domain: 'Finance.GL_Accounts', expected: 2400, actual: 2180, pct: 90.8, lastMig: '2026-04-01', status: 'warn' },
              { domain: 'Orders.Invoices', expected: 15200, actual: 14850, pct: 97.7, lastMig: '2026-04-10', status: 'ok' },
              { domain: 'People.Delegates_Logs', expected: 85000, actual: 42100, pct: 49.5, lastMig: '2026-03-15', status: 'bad' },
              { domain: 'Animations.Budgets_Approved', expected: 1200, actual: 890, pct: 74.2, lastMig: '2026-02-28', status: 'warn' },
              { domain: 'Market.Prescriber_Contacts', expected: 8900, actual: 7250, pct: 81.5, lastMig: '2026-01-20', status: 'warn' },
              { domain: 'Operations.Stock_Movements', expected: 125000, actual: 124200, pct: 99.4, lastMig: '2026-04-15', status: 'ok' },
            ].map((row, idx) => (
              <tr key={idx} className="border-b border-line/50 hover:bg-gray-50">
                <td className="py-2 font-mono text-xs font-medium">{row.domain}</td>
                <td className="text-right py-2 font-semibold">{row.expected.toLocaleString()}</td>
                <td className="text-right py-2">{row.actual.toLocaleString()}</td>
                <td className="text-right py-2 font-medium">{row.pct}%</td>
                <td className="py-2 text-xs text-mute">{row.lastMig}</td>
                <td className="text-center py-2">
                  <Pill variant={row.status as any} text={row.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
