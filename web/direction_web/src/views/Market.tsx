import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import { KpiCard } from '../components/KpiCard';
import { HeatmapGrid } from '../components/HeatmapGrid';
import { Pill } from '../components/Pill';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend);

export default function MarketDashboard() {
  const kpis = [
    { label: 'Zones', value: '79/79', delta: 100, deltaType: 'up' as const, barPercent: 100, barColor: 'bg-ok' },
    { label: 'White spots', value: '14 gov', delta: -12, deltaType: 'warn' as const, barPercent: 17.7, barColor: 'bg-warn' },
    { label: 'High-value rx', value: '1.3%', delta: 0.8, barPercent: 1.3, barColor: 'bg-ok' },
    { label: 'Priority pharma', value: '105', delta: 5.2, barPercent: 15, barColor: 'bg-info' },
  ];

  const gouvernorateValues = [92, 84, 71, 62, 58, 68, 41, 38, 35, 32, 28, 82, 74, 66, 58, 34, 32, 86, 42, 28, 26, 54, 48, 31];
  const gouvernorateNames = ['Tunis', 'Ariana', 'Ben Arous', 'Manouba', 'Bizerte', 'Nabeul', 'Zaghouan', 'Beja', 'Jendouba', 'Kef', 'Siliana', 'Sousse', 'Monastir', 'Mahdia', 'Kairouan', 'Kasserine', 'Sidi Bouzid', 'Sfax', 'Gafsa', 'Tozeur', 'Kebili', 'Gabes', 'Medenine', 'Tataouine'];

  const prescriberTiersData = {
    labels: ['Tier A', 'Tier B', 'Tier C', 'Tier D'],
    datasets: [{
      data: [85, 412, 2088, 3980],
      backgroundColor: ['#2C2C2A', '#5F5E5A', '#8F8E8A', '#D3D1C7'],
    }],
  };

  return (
    <div>
      <h1 className="text-3xl font-bold text-ink mb-1">Market & Geography</h1>
      <p className="text-mute text-sm mb-6">Geographic distribution and prescriber analysis</p>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {kpis.map((kpi, idx) => (
          <KpiCard
            key={idx}
            label={kpi.label}
            value={kpi.value}
            delta={kpi.delta}
            deltaType={kpi.deltaType}
            barPercent={kpi.barPercent}
            barColor={kpi.barColor}
          />
        ))}
      </div>

      {/* Heatmap + Prescriber Tiers */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <HeatmapGrid values={gouvernorateValues} names={gouvernorateNames} />
        <div className="bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">Prescriber tiers</h3>
          <div style={{ height: '260px' }}>
            <Doughnut data={prescriberTiersData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' as const } } }} />
          </div>
        </div>
      </div>

      {/* Priority Pharmacies Table */}
      <div className="bg-card border border-line rounded-lg p-5">
        <h3 className="text-lg font-semibold text-ink mb-4">Priority pharmacies</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line">
              <th className="text-left py-2 text-xs font-semibold text-mute">Pharmacy</th>
              <th className="text-left py-2 text-xs font-semibold text-mute">Gov</th>
              <th className="text-left py-2 text-xs font-semibold text-mute">Zone</th>
              <th className="text-right py-2 text-xs font-semibold text-mute">Potential CA</th>
              <th className="text-center py-2 text-xs font-semibold text-mute">Tier</th>
              <th className="text-center py-2 text-xs font-semibold text-mute">Elig.</th>
              <th className="text-center py-2 text-xs font-semibold text-mute">Action</th>
            </tr>
          </thead>
          <tbody>
            {[
              { name: 'Pharmacie Al-Farabi', gov: 'Tunis', zone: 'Tunis-Nord', ca: '2.8M', tier: 'A', elig: 'HIGH' },
              { name: 'Pharmacie Carthage', gov: 'Ariana', zone: 'Ariana-Central', ca: '2.2M', tier: 'A', elig: 'HIGH' },
              { name: 'Pharmacie Sfax Plus', gov: 'Sfax', zone: 'Sfax-Center', ca: '1.9M', tier: 'B', elig: 'MED' },
              { name: 'Pharmacie Sousse', gov: 'Sousse', zone: 'Sousse-Port', ca: '1.7M', tier: 'B', elig: 'MED' },
              { name: 'Pharmacie Med24', gov: 'Ben Arous', zone: 'Samarit', ca: '1.5M', tier: 'B', elig: 'MED' },
              { name: 'Pharmacie Kairouan', gov: 'Kairouan', zone: 'Kairouan-Old', ca: '1.2M', tier: 'C', elig: 'LOW' },
            ].map((row, idx) => (
              <tr key={idx} className="border-b border-line/50 hover:bg-gray-50">
                <td className="py-2 font-medium">{row.name}</td>
                <td className="py-2 text-xs text-mute">{row.gov}</td>
                <td className="py-2 text-xs">{row.zone}</td>
                <td className="text-right py-2 font-semibold">{row.ca}</td>
                <td className="text-center py-2">
                  <Pill variant="info" text={row.tier} />
                </td>
                <td className="text-center py-2">
                  <Pill variant={row.elig === 'HIGH' ? 'ok' : row.elig === 'MED' ? 'warn' : 'bad'} text={row.elig} />
                </td>
                <td className="text-center py-2 text-xs text-info font-medium cursor-pointer">Contact</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
