import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';
import { KpiCard } from '../components/KpiCard';
import { Pill } from '../components/Pill';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend);

export default function SupplyDashboard() {
  const kpis = [
    { label: 'Articles', value: '762', delta: 0, barPercent: 100, barColor: 'bg-info' },
    { label: 'Dead stock', value: '481', delta: -63, barPercent: 63, barColor: 'bg-ok' },
    { label: 'Expiring <90d', value: '124', delta: -12, deltaType: 'warn' as const, barPercent: 16.3, barColor: 'bg-warn' },
    { label: 'Gratuité rate', value: '15.7%', delta: 2.1, deltaType: 'down' as const, barPercent: 15.7, barColor: 'bg-bad' },
  ];

  const stockStatusData = {
    labels: ['Sain', 'At risk', 'Dead', 'Overstock'],
    datasets: [{
      data: [482, 162, 481, 219],
      backgroundColor: ['#1D9E75', '#BA7517', '#B8263E', '#7F77DD'],
    }],
  };

  const expiryTimelineData = {
    labels: ['<30d', '30-60d', '60-90d', '90-180d', '180-365d', '>1y'],
    datasets: [{
      label: 'Units',
      data: [42, 38, 44, 87, 124, 427],
      backgroundColor: ['#B8263E', '#B8263E', '#BA7517', '#378ADD', '#1D9E75', '#D3D1C7'],
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
      <h1 className="text-3xl font-bold text-ink mb-1">Supply & Stock</h1>
      <p className="text-mute text-sm mb-6">Inventory status and expiry management</p>

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
          <h3 className="text-lg font-semibold text-ink mb-4">Stock status</h3>
          <div style={{ height: '260px' }}>
            <Doughnut data={stockStatusData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' as const } } }} />
          </div>
        </div>
        <div className="bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">Expiry timeline</h3>
          <div style={{ height: '260px' }}>
            <Bar data={expiryTimelineData} options={chartOptions} />
          </div>
        </div>
      </div>

      {/* Dead Stock Table */}
      <div className="bg-card border border-line rounded-lg p-5">
        <h3 className="text-lg font-semibold text-ink mb-4">Dead stock items</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line">
              <th className="text-left py-2 text-xs font-semibold text-mute">SKU</th>
              <th className="text-right py-2 text-xs font-semibold text-mute">Qty</th>
              <th className="text-right py-2 text-xs font-semibold text-mute">Value DT</th>
              <th className="text-right py-2 text-xs font-semibold text-mute">Days zero</th>
              <th className="text-left py-2 text-xs font-semibold text-mute">Expiry</th>
              <th className="text-center py-2 text-xs font-semibold text-mute">Action</th>
            </tr>
          </thead>
          <tbody>
            {[
              { sku: 'SKU001', qty: 480, value: 12800, days: 342, expiry: '2023-06-15' },
              { sku: 'SKU002', qty: 320, value: 8960, days: 285, expiry: '2023-08-22' },
              { sku: 'SKU003', qty: 210, value: 6300, days: 198, expiry: '2023-11-14' },
              { sku: 'SKU004', qty: 180, value: 5400, days: 156, expiry: '2024-01-25' },
              { sku: 'SKU005', qty: 150, value: 4200, days: 128, expiry: '2024-02-22' },
              { sku: 'SKU006', qty: 120, value: 3600, days: 95, expiry: '2024-03-27' },
            ].map((row, idx) => (
              <tr key={idx} className="border-b border-line/50 hover:bg-gray-50">
                <td className="py-2 font-mono text-xs font-semibold">{row.sku}</td>
                <td className="text-right py-2">{row.qty}</td>
                <td className="text-right py-2 font-medium">{row.value} DT</td>
                <td className="text-right py-2">
                  <Pill variant={row.days > 365 ? 'bad' : row.days > 180 ? 'warn' : 'info'} text={`${row.days}d`} />
                </td>
                <td className="py-2 text-xs">{row.expiry}</td>
                <td className="text-center py-2 text-xs text-info font-medium cursor-pointer">Destroy</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
