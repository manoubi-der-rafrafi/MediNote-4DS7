import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { KpiCard } from '../components/KpiCard';
import { MiniBar } from '../components/MiniBar';
import { Pill } from '../components/Pill';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function PeopleDashboard() {
  const kpis = [
    { label: 'Active delegates', value: '143', delta: 2.2, barPercent: 100, barColor: 'bg-ok' },
    { label: 'High performers', value: '38', delta: 26.6, barPercent: 26.6, barColor: 'bg-ok' },
    { label: 'Attrition risk', value: '17', delta: -8.5, deltaType: 'warn' as const, barPercent: 11.9, barColor: 'bg-warn' },
    { label: 'Formation ROI', value: '+14.2%', delta: 8.9, barPercent: 42.6, barColor: 'bg-ok' },
  ];

  const supervisorRankingData = {
    labels: ['Sup1', 'Sup2', 'Sup3', 'Sup4', 'Sup5', 'Sup6', 'Sup7', 'Sup8', 'Sup9', 'Sup10', 'Sup11', 'Sup12'],
    datasets: [{
      label: 'Score',
      data: [94, 91, 87, 84, 79, 76, 72, 68, 65, 61, 58, 55],
      backgroundColor: (ctx: any) => {
        const value = ctx.parsed.y;
        if (value >= 75) return '#1D9E75';
        if (value >= 60) return '#378ADD';
        if (value >= 50) return '#BA7517';
        return '#B8263E';
      },
      borderRadius: 4,
    }],
  };

  const chartOptions = {
    indexAxis: 'y' as const,
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: { x: { grid: { drawTicks: false } }, y: { grid: { display: false } } },
  };

  return (
    <div>
      <h1 className="text-3xl font-bold text-ink mb-1">People & Delegates</h1>
      <p className="text-mute text-sm mb-6">Delegate performance and team management</p>

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

      {/* Supervisor ranking */}
      <div className="bg-card border border-line rounded-lg p-5 mb-6">
        <h3 className="text-lg font-semibold text-ink mb-4">Supervisor ranking</h3>
        <div style={{ height: '260px' }}>
          <Bar data={supervisorRankingData} options={chartOptions} />
        </div>
      </div>

      {/* Delegates Table */}
      <div className="bg-card border border-line rounded-lg p-5">
        <h3 className="text-lg font-semibold text-ink mb-4">Top delegates</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line">
              <th className="text-left py-2 text-xs font-semibold text-mute">Name</th>
              <th className="text-left py-2 text-xs font-semibold text-mute">Supervisor</th>
              <th className="text-left py-2 text-xs font-semibold text-mute">Zone</th>
              <th className="text-center py-2 text-xs font-semibold text-mute">CA vs Obj</th>
              <th className="text-right py-2 text-xs font-semibold text-mute">Prime %</th>
              <th className="text-center py-2 text-xs font-semibold text-mute">Quality</th>
              <th className="text-center py-2 text-xs font-semibold text-mute">Risk</th>
            </tr>
          </thead>
          <tbody>
            {[
              { name: 'Ahmed B.', sup: 'Karim', zone: 'Tunis-N', ca: 8.5, caObj: 8.0, prime: 48, quality: 85, risk: 'low' },
              { name: 'Fatima E.', sup: 'Nadia', zone: 'Sfax-C', ca: 7.2, caObj: 7.0, prime: 52, quality: 92, risk: 'low' },
              { name: 'Mohamed K.', sup: 'Hassan', zone: 'Tunis-S', ca: 6.8, caObj: 7.5, prime: 44, quality: 78, risk: 'high' },
              { name: 'Leila M.', sup: 'Karim', zone: 'Ariana', ca: 9.1, caObj: 8.5, prime: 55, quality: 88, risk: 'low' },
              { name: 'Karim R.', sup: 'Rania', zone: 'Sousse', ca: 5.5, caObj: 6.2, prime: 38, quality: 65, risk: 'high' },
              { name: 'Nadia S.', sup: 'Hassan', zone: 'Nabeul', ca: 6.2, caObj: 6.0, prime: 50, quality: 82, risk: 'medium' },
            ].map((row, idx) => (
              <tr key={idx} className="border-b border-line/50 hover:bg-gray-50">
                <td className="py-2 font-medium">{row.name}</td>
                <td className="py-2 text-xs text-mute">{row.sup}</td>
                <td className="py-2 text-xs">{row.zone}</td>
                <td className="py-2 text-center">
                  <MiniBar percent={(row.ca / row.caObj) * 100} color="bg-info" />
                </td>
                <td className="text-right py-2 font-semibold">{row.prime}%</td>
                <td className="text-center py-2">
                  <Pill variant={row.quality >= 80 ? 'ok' : row.quality >= 70 ? 'info' : 'warn'} text={`${row.quality}%`} />
                </td>
                <td className="text-center py-2">
                  <Pill variant={row.risk === 'low' ? 'ok' : row.risk === 'medium' ? 'warn' : 'bad'} text={row.risk} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
