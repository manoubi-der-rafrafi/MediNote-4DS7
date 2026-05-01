import { useState, useEffect } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';
import { KpiCard } from '../components/KpiCard';
import { Pill } from '../components/Pill';
import { Chip } from '../components/Chip';
import { delegates } from '../data/delegates';

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend, Filler);

export function VisitQuality() {
  const [chartsInit, setChartsInit] = useState(false);

  useEffect(() => {
    setChartsInit(true);
  }, []);

  // Quality distribution
  const aCount = delegates.filter((d) => d.q === 'A').length;
  const bCount = delegates.filter((d) => d.q === 'B').length;
  const cCount = delegates.filter((d) => d.q === 'C').length;
  const dCount = delegates.filter((d) => d.q === 'D').length;
  const total = delegates.length;

  // Stacked bar data - quality per delegate
  const qualityPerDelegateData: any = {
    labels: delegates.map((d) => d.init),
    datasets: [
      {
        label: 'A-tier',
        data: delegates.map((d) => (d.q === 'A' ? 80 : d.q === 'B' ? 40 : d.q === 'C' ? 15 : 5)),
        backgroundColor: '#1D9E75',
      },
      {
        label: 'B-tier',
        data: delegates.map((d) => (d.q === 'A' ? 15 : d.q === 'B' ? 45 : d.q === 'C' ? 30 : 15)),
        backgroundColor: '#378ADD',
      },
      {
        label: 'C-tier',
        data: delegates.map((d) => (d.q === 'A' ? 4 : d.q === 'B' ? 12 : d.q === 'C' ? 40 : 30)),
        backgroundColor: '#BA7517',
      },
      {
        label: 'D-tier',
        data: delegates.map((d) => (d.q === 'A' ? 1 : d.q === 'B' ? 3 : d.q === 'C' ? 15 : 50)),
        backgroundColor: '#B8263E',
      },
    ],
  };

  const qualityPerDelegateOptions = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'x' as const,
    stacked: true,
    plugins: {
      legend: { position: 'bottom' as const, boxWidth: 10 },
      title: { display: true, text: 'Quality per Delegate' },
    },
    scales: {
      y: { stacked: true, max: 100, title: { display: true, text: '% of Reports' }, grid: { color: '#E5E4DE' } },
      x: { stacked: true, grid: { display: false } },
    },
  };

  // Trend line
  const trendData = {
    labels: ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8', 'W9', 'W10', 'W11', 'W12'],
    datasets: [
      {
        label: 'A-tier %',
        data: [28, 30, 31, 32, 31, 33, 32, 34, 33, 35, 34, 34],
        borderColor: '#1D9E75',
        backgroundColor: 'rgba(29, 158, 117, 0.1)',
        fill: true,
        tension: 0.4,
        borderWidth: 2,
      },
      {
        label: 'D-tier %',
        data: [9, 8, 8, 7, 8, 7, 7, 6, 7, 6, 6, 6],
        borderColor: '#B8263E',
        backgroundColor: 'rgba(184, 38, 62, 0.1)',
        fill: true,
        tension: 0.4,
        borderWidth: 2,
      },
    ],
  };

  const trendOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom' as const, boxWidth: 10 },
      title: { display: true, text: 'Quality Trend · 12 Weeks' },
    },
    scales: {
      y: { title: { display: true, text: 'Percentage %' }, grid: { color: '#E5E4DE' } },
    },
  };

  if (!chartsInit) return <div>Loading...</div>;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-22 font-bold text-ink mb-1">Visit Quality</h1>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard
          label="A-tier Reports"
          value={`${((aCount / total) * 100).toFixed(0)}%`}
          delta={2}
          deltaType="up"
          barPercent={(aCount / total) * 100}
          barColor="bg-ok"
        />
        <KpiCard
          label="B-tier"
          value={`${((bCount / total) * 100).toFixed(0)}%`}
          delta={0}
          deltaType="neutral"
          barPercent={(bCount / total) * 100}
          barColor="bg-brand"
        />
        <KpiCard
          label="C-tier"
          value={`${((cCount / total) * 100).toFixed(0)}%`}
          delta={-1}
          deltaType="warn"
          barPercent={(cCount / total) * 100}
          barColor="bg-warn"
        />
        <KpiCard
          label="D-tier"
          value={`${((dCount / total) * 100).toFixed(0)}%`}
          delta={-1}
          deltaType="warn"
          barPercent={(dCount / total) * 100}
          barColor="bg-bad"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-card rounded-lg p-4 border border-line" style={{ height: 300 }}>
          <Bar data={qualityPerDelegateData} options={qualityPerDelegateOptions} />
        </div>
        <div className="bg-card rounded-lg p-4 border border-line" style={{ height: 300 }}>
          <Line data={trendData} options={trendOptions} />
        </div>
      </div>

      {/* Recent Reports */}
      <div className="bg-card rounded-lg border border-line overflow-hidden">
        <div className="p-4 border-b border-line bg-brand-soft">
          <h2 className="text-13 font-semibold text-ink">Recent Reports Reviewed</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-line">
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Date</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Delegate</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Pharmacy</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Quality</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Words</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Tags</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-line hover:bg-brand-soft">
                <td className="px-4 py-3 text-sm text-mute">18 Apr</td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">A. Khelifi</td>
                <td className="px-4 py-3 text-sm text-mute">Pharm. Carthage</td>
                <td className="px-4 py-3"><Pill variant="ok" text="A" /></td>
                <td className="px-4 py-3 text-sm text-mute">324</td>
                <td className="px-4 py-3"><Chip variant="info" text="conseil" /></td>
                <td className="px-4 py-3"><Chip variant="ok" text="Approve" /></td>
              </tr>
              <tr className="border-b border-line hover:bg-brand-soft">
                <td className="px-4 py-3 text-sm text-mute">17 Apr</td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">S. Ben Salah</td>
                <td className="px-4 py-3 text-sm text-mute">Pharm. El Manar</td>
                <td className="px-4 py-3"><Pill variant="ok" text="A" /></td>
                <td className="px-4 py-3 text-sm text-mute">287</td>
                <td className="px-4 py-3 flex gap-1"><Chip variant="info" text="conseil" /><Chip variant="info" text="formation" /></td>
                <td className="px-4 py-3"><Chip variant="ok" text="Approve" /></td>
              </tr>
              <tr className="border-b border-line hover:bg-brand-soft">
                <td className="px-4 py-3 text-sm text-mute">17 Apr</td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">M. Gharbi</td>
                <td className="px-4 py-3 text-sm text-mute">Pharm. Sahloul</td>
                <td className="px-4 py-3"><Pill variant="info" text="B" /></td>
                <td className="px-4 py-3 text-sm text-mute">198</td>
                <td className="px-4 py-3"><Chip variant="warn" text="concurrence" /></td>
                <td className="px-4 py-3"><Chip variant="ok" text="Approve" /></td>
              </tr>
              <tr className="border-b border-line hover:bg-brand-soft">
                <td className="px-4 py-3 text-sm text-mute">16 Apr</td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">K. Tounsi</td>
                <td className="px-4 py-3 text-sm text-mute">Pharm. Kairouan-N</td>
                <td className="px-4 py-3"><Pill variant="warn" text="C" /></td>
                <td className="px-4 py-3 text-sm text-mute">82</td>
                <td className="px-4 py-3"><Chip variant="warn" text="stock" /></td>
                <td className="px-4 py-3"><Chip variant="warn" text="Review" /></td>
              </tr>
              <tr className="border-b border-line hover:bg-brand-soft">
                <td className="px-4 py-3 text-sm text-mute">16 Apr</td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">N. Ayari</td>
                <td className="px-4 py-3 text-sm text-mute">Pharm. Médenine-S</td>
                <td className="px-4 py-3"><Pill variant="bad" text="D" /></td>
                <td className="px-4 py-3 text-sm text-mute">41</td>
                <td className="px-4 py-3"><Chip variant="bad" text="3 flags" /></td>
                <td className="px-4 py-3"><Chip variant="bad" text="Reject" /></td>
              </tr>
              <tr className="hover:bg-brand-soft">
                <td className="px-4 py-3 text-sm text-mute">15 Apr</td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">H. Zouari</td>
                <td className="px-4 py-3 text-sm text-mute">Pharm. Gabès-C</td>
                <td className="px-4 py-3"><Pill variant="bad" text="D" /></td>
                <td className="px-4 py-3 text-sm text-mute">28</td>
                <td className="px-4 py-3"><Chip variant="bad" text="4 flags" /></td>
                <td className="px-4 py-3"><Chip variant="bad" text="Reject" /></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
