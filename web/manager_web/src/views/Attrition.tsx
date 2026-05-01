import { useState, useEffect } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';
import { KpiCard } from '../components/KpiCard';
import { AlertBox } from '../components/AlertBox';
import { Avatar } from '../components/Avatar';
import { Pill } from '../components/Pill';
import { Chip } from '../components/Chip';

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend);

export function Attrition() {
  const [chartsInit, setChartsInit] = useState(false);

  useEffect(() => {
    setChartsInit(true);
  }, []);

  // Distribution chart
  const distributionData = {
    labels: ['<0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '>0.8'],
    datasets: [
      {
        label: 'Delegates',
        data: [4, 7, 4, 1, 2],
        backgroundColor: ['#1D9E75', '#1D9E75', '#BA7517', '#B8263E', '#B8263E'],
        borderRadius: 4,
      },
    ],
  };

  const distributionOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom' as const, boxWidth: 10 },
      title: { display: true, text: 'Attrition Score Distribution' },
    },
    scales: {
      y: { title: { display: true, text: 'Count' }, grid: { color: '#E5E4DE' } },
    },
  };

  // Trend line for at-risk delegates
  const trendData = {
    labels: ['Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr'],
    datasets: [
      {
        label: 'HZ (Hichem Zouari)',
        data: [0.52, 0.58, 0.68, 0.76, 0.85, 0.91],
        borderColor: '#B8263E',
        borderWidth: 2,
        tension: 0.4,
        fill: false,
      },
      {
        label: 'NA (Najla Ayari)',
        data: [0.45, 0.52, 0.61, 0.71, 0.78, 0.84],
        borderColor: '#BA7517',
        borderWidth: 2,
        tension: 0.4,
        fill: false,
      },
      {
        label: 'KT (Khaled Tounsi)',
        data: [0.38, 0.43, 0.51, 0.58, 0.62, 0.67],
        borderColor: '#7F77DD',
        borderWidth: 2,
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
      title: { display: true, text: 'Score Trend · At-Risk Delegates' },
    },
    scales: {
      y: { min: 0, max: 1, title: { display: true, text: 'Risk Score' }, grid: { color: '#E5E4DE' } },
    },
  };

  if (!chartsInit) return <div>Loading...</div>;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-22 font-bold text-ink mb-1">Attrition Risk</h1>
      </div>

      {/* Alert */}
      <div className="mb-6">
        <AlertBox message="3 delegates at high attrition risk — composite score (CA + visit Q + comment quality + prime) has declined 3 consecutive months. Intervention window: next 30 days." />
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard
          label="High Risk"
          value="3"
          delta={0}
          deltaType="down"
          barPercent={17}
          barColor="bg-bad"
        />
        <KpiCard
          label="Medium Risk"
          value="4"
          delta={0}
          deltaType="down"
          barPercent={22}
          barColor="bg-warn"
        />
        <KpiCard
          label="Stable"
          value="11/18"
          delta={0}
          deltaType="up"
          barPercent={61}
          barColor="bg-ok"
        />
        <KpiCard
          label="Predicted Exits"
          value="2 ±1"
          delta={0}
          deltaType="down"
          barPercent={11}
          barColor="bg-warn"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-card rounded-lg p-4 border border-line" style={{ height: 300 }}>
          <Bar data={distributionData} options={distributionOptions} />
        </div>
        <div className="bg-card rounded-lg p-4 border border-line" style={{ height: 300 }}>
          <Line data={trendData} options={trendOptions} />
        </div>
      </div>

      {/* Table */}
      <div className="bg-card rounded-lg border border-line overflow-hidden">
        <div className="p-4 border-b border-line bg-brand-soft">
          <h2 className="text-13 font-semibold text-ink">At-Risk Delegates · Action Plan</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-line">
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Delegate</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Risk Score</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Trend</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">CA %</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Visit Q</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Status</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-line hover:bg-brand-soft" style={{ backgroundColor: '#FCEBEB' }}>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Avatar init="HZ" name="Hichem Zouari" />
                    <span className="text-sm font-semibold text-ink">Hichem Zouari</span>
                  </div>
                </td>
                <td className="px-4 py-3"><Pill variant="bad" text="0.91" /></td>
                <td className="px-4 py-3 text-sm font-semibold" style={{ color: 'var(--bad)' }}>▼▼▼</td>
                <td className="px-4 py-3 text-sm text-mute">19%</td>
                <td className="px-4 py-3"><Pill variant="bad" text="D" /></td>
                <td className="px-4 py-3 text-xs text-mute">Declining 4 mo</td>
                <td className="px-4 py-3"><Chip variant="bad" text="Urgent 1:1 · retention offer" /></td>
              </tr>
              <tr className="border-b border-line hover:bg-brand-soft" style={{ backgroundColor: '#FCEBEB' }}>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Avatar init="NA" name="Najla Ayari" />
                    <span className="text-sm font-semibold text-ink">Najla Ayari</span>
                  </div>
                </td>
                <td className="px-4 py-3"><Pill variant="bad" text="0.84" /></td>
                <td className="px-4 py-3 text-sm font-semibold" style={{ color: 'var(--bad)' }}>▼▼</td>
                <td className="px-4 py-3 text-sm text-mute">28%</td>
                <td className="px-4 py-3"><Pill variant="bad" text="D" /></td>
                <td className="px-4 py-3 text-xs text-mute">Declining 3 mo</td>
                <td className="px-4 py-3"><Chip variant="bad" text="Territory reassign · formation" /></td>
              </tr>
              <tr className="border-b border-line hover:bg-brand-soft" style={{ backgroundColor: '#FCEBEB' }}>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Avatar init="KT" name="Khaled Tounsi" />
                    <span className="text-sm font-semibold text-ink">Khaled Tounsi</span>
                  </div>
                </td>
                <td className="px-4 py-3"><Pill variant="warn" text="0.67" /></td>
                <td className="px-4 py-3 text-sm font-semibold" style={{ color: 'var(--warn)' }}>▼</td>
                <td className="px-4 py-3 text-sm text-mute">42%</td>
                <td className="px-4 py-3"><Pill variant="warn" text="C" /></td>
                <td className="px-4 py-3 text-xs text-mute">Comments dropping</td>
                <td className="px-4 py-3"><Chip variant="warn" text="Coaching + formation γ-3" /></td>
              </tr>
              <tr className="border-b border-line hover:bg-brand-soft">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Avatar init="SM" name="Skander Mejri" />
                    <span className="text-sm font-semibold text-ink">Skander Mejri</span>
                  </div>
                </td>
                <td className="px-4 py-3"><Pill variant="warn" text="0.58" /></td>
                <td className="px-4 py-3 text-sm font-semibold" style={{ color: 'var(--warn)' }}>▼</td>
                <td className="px-4 py-3 text-sm text-mute">54%</td>
                <td className="px-4 py-3"><Pill variant="warn" text="C" /></td>
                <td className="px-4 py-3 text-xs text-mute">Lost 4 accounts</td>
                <td className="px-4 py-3"><Chip variant="warn" text="Shadow visits · formation" /></td>
              </tr>
              <tr className="hover:bg-brand-soft">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Avatar init="LM" name="Leila Mansouri" />
                    <span className="text-sm font-semibold text-ink">Leila Mansouri</span>
                  </div>
                </td>
                <td className="px-4 py-3"><Pill variant="warn" text="0.51" /></td>
                <td className="px-4 py-3 text-sm font-semibold text-mute">—</td>
                <td className="px-4 py-3 text-sm text-mute">49%</td>
                <td className="px-4 py-3"><Pill variant="warn" text="C" /></td>
                <td className="px-4 py-3 text-xs text-mute">Report quality drop</td>
                <td className="px-4 py-3"><Chip variant="warn" text="Shadow visit next week" /></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
