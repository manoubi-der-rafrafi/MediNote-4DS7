import { Chart as ChartJS, CategoryScale, LinearScale, LineElement, PointElement, BarElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import { KpiCard } from '../components/KpiCard';
import { Pill } from '../components/Pill';

ChartJS.register(CategoryScale, LinearScale, LineElement, PointElement, BarElement, Title, Tooltip, Legend, Filler);

export default function ForecastsDashboard() {
  const kpis = [
    { label: 'Q2 forecast', value: '58.7M DT', delta: 6.2, barPercent: 58.7, barColor: 'bg-ok' },
    { label: 'Expiry loss', value: '2.4M DT', delta: -2.4, deltaType: 'warn' as const, barPercent: 2.4, barColor: 'bg-bad' },
    { label: 'Delegates miss', value: '38/143', delta: -26.6, deltaType: 'warn' as const, barPercent: 26.6, barColor: 'bg-warn' },
    { label: 'Attrition risk', value: '17', delta: -11.9, barPercent: 11.9, barColor: 'bg-warn' },
  ];

  // Revenue forecast with confidence bands
  const forecastData = {
    labels: ['Q1 Act', 'Q2', 'Q3', 'Q4'],
    datasets: [
      {
        label: 'Forecast',
        data: [52.4, 58.7, 61.2, 64.8],
        borderColor: '#378ADD',
        backgroundColor: 'rgba(55, 138, 221, 0.1)',
        fill: true,
        tension: 0.3,
      },
      {
        label: 'Upper 95%',
        data: [56.2, 63.1, 65.8, 69.5],
        borderColor: '#1D9E75',
        borderDash: [5, 5],
        fill: false,
        pointRadius: 0,
      },
      {
        label: 'Lower 95%',
        data: [48.6, 54.3, 56.6, 60.1],
        borderColor: '#BA7517',
        borderDash: [5, 5],
        fill: false,
        pointRadius: 0,
      },
    ],
  };

  // Expiry loss by month
  const expiryLossData = {
    labels: ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    datasets: [{
      label: 'Loss (K DT)',
      data: [280, 420, 320, 180, 150, 220, 310, 270, 190],
      backgroundColor: (ctx: any) => {
        const value = ctx.parsed.y;
        if (value > 300) return '#B8263E';
        if (value > 200) return '#BA7517';
        return '#378ADD';
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
      <p className="text-mute text-sm mb-6">ML predictions with confidence bands</p>

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
          <h3 className="text-lg font-semibold text-ink mb-4">Revenue forecast (M DT)</h3>
          <div style={{ height: '260px' }}>
            <Line data={forecastData} options={chartOptions} />
          </div>
        </div>
        <div className="bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">Expiry loss by month</h3>
          <div style={{ height: '260px' }}>
            <Bar data={expiryLossData} options={chartOptions} />
          </div>
        </div>
      </div>

      {/* Model Predictions Table */}
      <div className="bg-card border border-line rounded-lg p-5">
        <h3 className="text-lg font-semibold text-ink mb-4">Model predictions</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line">
              <th className="text-left py-2 text-xs font-semibold text-mute">Model</th>
              <th className="text-right py-2 text-xs font-semibold text-mute">Metric</th>
              <th className="text-left py-2 text-xs font-semibold text-mute">Horizon</th>
              <th className="text-left py-2 text-xs font-semibold text-mute">Output</th>
              <th className="text-center py-2 text-xs font-semibold text-mute">Status</th>
            </tr>
          </thead>
          <tbody>
            {[
              { model: 'Revenue ARIMA', metric: 'MAPE', val: '3.2%', horizon: 'Q2-Q4 2026', output: 'Point forecast', status: 'ok' },
              { model: 'Delegate Churn', metric: 'AUC', val: '0.89', horizon: 'Next 90d', output: 'Risk scores', status: 'ok' },
              { model: 'Anomaly Detector', metric: 'Precision', val: '91%', horizon: 'Real-time', output: 'Flag scores', status: 'ok' },
              { model: 'Expiry Predictor', metric: 'R²', val: '0.84', horizon: 'Q2-Q4 2026', output: 'Loss forecast', status: 'ok' },
              { model: 'Animation ROI', metric: 'AUC', val: '1.00', horizon: 'Pre-approval', output: 'P(strong)', status: 'ok' },
              { model: 'Market Trend', metric: 'Theil-U', val: '0.12', horizon: '6-month', output: 'Direction', status: 'warn' },
              { model: 'Stock DOI', metric: 'RMSE', val: '8.4 days', horizon: 'Next 60d', output: 'Turnover', status: 'ok' },
              { model: 'Prime Simulator', metric: 'Linear', val: 'N/A', horizon: 'What-if', output: 'Payout', status: 'info' },
            ].map((row, idx) => (
              <tr key={idx} className="border-b border-line/50 hover:bg-gray-50">
                <td className="py-2 font-medium">{row.model}</td>
                <td className="text-right py-2 font-semibold">{row.val}</td>
                <td className="py-2 text-xs text-mute">{row.horizon}</td>
                <td className="py-2 text-xs">{row.output}</td>
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
