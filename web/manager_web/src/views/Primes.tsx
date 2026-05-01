import { useState, useEffect } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';
import { KpiCard } from '../components/KpiCard';
import { MiniBar } from '../components/MiniBar';
import { Pill } from '../components/Pill';
import { delegates } from '../data/delegates';

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend, Filler);

export function Primes() {
  const [chartsInit, setChartsInit] = useState(false);

  useEffect(() => {
    setChartsInit(true);
  }, []);

  // Prime bar chart
  const primeData = {
    labels: delegates.map((d) => d.init),
    datasets: [
      {
        label: 'Prime %',
        data: delegates.map((d) => d.prime),
        backgroundColor: delegates.map((d) =>
          d.prime >= 75 ? '#1D9E75' : d.prime >= 50 ? '#378ADD' : d.prime >= 30 ? '#BA7517' : '#B8263E'
        ),
        borderRadius: 4,
      },
    ],
  };

  const primeOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom' as const, boxWidth: 10 },
      title: { display: true, text: 'Prime % per Delegate' },
    },
    scales: {
      y: { title: { display: true, text: 'Prime %' }, max: 100, grid: { color: '#E5E4DE' } },
    },
  };

  // Trend line
  const trendData = {
    labels: ['Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr'],
    datasets: [
      {
        label: 'Team Avg',
        data: [48, 51, 53, 56, 57, 58],
        borderColor: '#BA7517',
        borderWidth: 2,
        tension: 0.4,
        fill: false,
      },
      {
        label: 'Platform Avg',
        data: [52, 53, 54, 53, 53, 53],
        borderColor: '#6B6B66',
        borderWidth: 2,
        borderDash: [5, 5],
        tension: 0.4,
        fill: false,
      },
    ],
  };

  const trendOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom' as const, boxWidth: 10 },
      title: { display: true, text: 'Prime Trend · 6 Months' },
    },
    scales: {
      y: { max: 100, grid: { color: '#E5E4DE' } },
    },
  };

  if (!chartsInit) return <div>Loading...</div>;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-22 font-bold text-ink mb-1">Primes & Bonus</h1>
        <p className="text-xs text-mute">Team realization 58.1% · vs platform avg 53.4%</p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard
          label="Team Prime Pool"
          value="162K DT"
          delta={0}
          deltaType="neutral"
          barPercent={100}
          barColor="bg-brand"
        />
        <KpiCard
          label="Realized"
          value="94.2K DT"
          delta={5}
          deltaType="up"
          barPercent={58}
          barColor="bg-ok"
        />
        <KpiCard
          label="Top Earner"
          value="A. Khelifi"
          delta={0}
          deltaType="up"
          barPercent={94}
          barColor="bg-ok"
        />
        <KpiCard
          label="At 0%"
          value="2"
          delta={0}
          deltaType="down"
          barPercent={11}
          barColor="bg-bad"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-card rounded-lg p-4 border border-line" style={{ height: 300 }}>
          <Bar data={primeData} options={primeOptions} />
        </div>
        <div className="bg-card rounded-lg p-4 border border-line" style={{ height: 300 }}>
          <Line data={trendData} options={trendOptions} />
        </div>
      </div>

      {/* Table */}
      <div className="bg-card rounded-lg border border-line overflow-hidden">
        <div className="p-4 border-b border-line bg-brand-soft">
          <h2 className="text-13 font-semibold text-ink">Detailed Prime Breakdown</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-line">
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Delegate</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Max</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">%</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Realized</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">CA Hit</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Visit Q Hit</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-line hover:bg-brand-soft">
                <td className="px-4 py-3 text-sm font-semibold text-ink">A. Khelifi</td>
                <td className="px-4 py-3 text-sm text-mute">12K DT</td>
                <td className="px-4 py-3"><MiniBar percent={94} color="bg-ok" /></td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">11.3K</td>
                <td className="px-4 py-3"><Pill variant="ok" text="Hit" /></td>
                <td className="px-4 py-3"><Pill variant="ok" text="Hit" /></td>
                <td className="px-4 py-3"><Pill variant="ok" text="Paid" /></td>
              </tr>
              <tr className="border-b border-line hover:bg-brand-soft">
                <td className="px-4 py-3 text-sm font-semibold text-ink">S. Ben Salah</td>
                <td className="px-4 py-3 text-sm text-mute">12K DT</td>
                <td className="px-4 py-3"><MiniBar percent={88} color="bg-ok" /></td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">10.6K</td>
                <td className="px-4 py-3"><Pill variant="ok" text="Hit" /></td>
                <td className="px-4 py-3"><Pill variant="ok" text="Hit" /></td>
                <td className="px-4 py-3"><Pill variant="ok" text="Paid" /></td>
              </tr>
              <tr className="border-b border-line hover:bg-brand-soft">
                <td className="px-4 py-3 text-sm font-semibold text-ink">M. Gharbi</td>
                <td className="px-4 py-3 text-sm text-mute">10K DT</td>
                <td className="px-4 py-3"><MiniBar percent={71} color="bg-info" /></td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">7.1K</td>
                <td className="px-4 py-3"><Pill variant="info" text="Partial" /></td>
                <td className="px-4 py-3"><Pill variant="ok" text="Hit" /></td>
                <td className="px-4 py-3"><Pill variant="ok" text="Paid" /></td>
              </tr>
              <tr className="border-b border-line hover:bg-brand-soft">
                <td className="px-4 py-3 text-sm font-semibold text-ink">K. Tounsi</td>
                <td className="px-4 py-3 text-sm text-mute">10K DT</td>
                <td className="px-4 py-3"><MiniBar percent={42} color="bg-warn" /></td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">4.2K</td>
                <td className="px-4 py-3"><Pill variant="warn" text="Miss" /></td>
                <td className="px-4 py-3"><Pill variant="warn" text="Partial" /></td>
                <td className="px-4 py-3"><Pill variant="warn" text="Reduced" /></td>
              </tr>
              <tr className="border-b border-line hover:bg-brand-soft">
                <td className="px-4 py-3 text-sm font-semibold text-ink">N. Ayari</td>
                <td className="px-4 py-3 text-sm text-mute">8K DT</td>
                <td className="px-4 py-3"><MiniBar percent={28} color="bg-bad" /></td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">2.2K</td>
                <td className="px-4 py-3"><Pill variant="bad" text="Miss" /></td>
                <td className="px-4 py-3"><Pill variant="bad" text="Miss" /></td>
                <td className="px-4 py-3"><Pill variant="bad" text="Reduced" /></td>
              </tr>
              <tr className="hover:bg-brand-soft">
                <td className="px-4 py-3 text-sm font-semibold text-ink">H. Zouari</td>
                <td className="px-4 py-3 text-sm text-mute">8K DT</td>
                <td className="px-4 py-3"><MiniBar percent={19} color="bg-bad" /></td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">1.5K</td>
                <td className="px-4 py-3"><Pill variant="bad" text="Miss" /></td>
                <td className="px-4 py-3"><Pill variant="bad" text="Miss" /></td>
                <td className="px-4 py-3"><Pill variant="bad" text="Reduced" /></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
