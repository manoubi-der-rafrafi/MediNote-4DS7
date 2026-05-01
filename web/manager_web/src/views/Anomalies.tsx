import { useState, useEffect } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, LineElement, PointElement, BarElement, ArcElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { Line, Doughnut } from 'react-chartjs-2';
import { KpiCard } from '../components/KpiCard';
import { Pill } from '../components/Pill';
import { Chip } from '../components/Chip';

ChartJS.register(CategoryScale, LinearScale, LineElement, PointElement, BarElement, ArcElement, Title, Tooltip, Legend, Filler);

export function Anomalies() {
  const [chartsInit, setChartsInit] = useState(false);

  useEffect(() => {
    setChartsInit(true);
  }, []);

  const trendData = {
    labels: ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8', 'W9', 'W10', 'W11', 'W12'],
    datasets: [
      {
        label: 'Anomaly Rate %',
        data: [5.2, 4.8, 5.5, 6.1, 7.2, 6.8, 7.5, 7.1, 6.9, 6.4, 6.3, 6.2],
        borderColor: '#B8263E',
        backgroundColor: 'rgba(184, 38, 62, 0.15)',
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
      legend: { display: false },
      title: { display: true, text: 'Anomaly Trend (12w)' },
    },
    scales: {
      y: { grid: { color: '#E5E4DE' } },
    },
  };

  const typeData = {
    labels: ['Inflated+', 'Contradiction', 'Duplicate', 'Sparse', 'Off-territory'],
    datasets: [
      {
        data: [7, 5, 3, 2, 1],
        backgroundColor: ['#B8263E', '#BA7517', '#7F77DD', '#378ADD', '#E5E4DE'],
      },
    ],
  };

  const typeOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom' as const, boxWidth: 10 },
      title: { display: true, text: 'By Type' },
    },
    cutout: '62%',
  };

  if (!chartsInit) return <div>Loading...</div>;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-22 font-bold text-ink mb-1">Anomalies</h1>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard
          label="Flagged Reports"
          value="18"
          delta={0}
          deltaType="warn"
          barPercent={62}
          barColor="bg-warn"
        />
        <KpiCard
          label="Avg Anomaly Score"
          value="0.21"
          delta={0}
          deltaType="neutral"
          barPercent={21}
          barColor="bg-brand"
        />
        <KpiCard
          label="Contradictions"
          value="7"
          delta={0}
          deltaType="warn"
          barPercent={39}
          barColor="bg-bad"
        />
        <KpiCard
          label="Delegates Flagged"
          value="4/18"
          delta={0}
          deltaType="warn"
          barPercent={22}
          barColor="bg-warn"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-card rounded-lg p-4 border border-line" style={{ height: 300 }}>
          <Line data={trendData} options={trendOptions} />
        </div>
        <div className="bg-card rounded-lg p-4 border border-line" style={{ height: 300 }}>
          <Doughnut data={typeData} options={typeOptions} />
        </div>
      </div>

      {/* Table */}
      <div className="bg-card rounded-lg border border-line overflow-hidden">
        <div className="p-4 border-b border-line bg-brand-soft">
          <h2 className="text-13 font-semibold text-ink">Flagged Reports</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-line">
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Date</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Delegate</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Pharmacy</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Type</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Score</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Details</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-line hover:bg-brand-soft" style={{ backgroundColor: '#FCEBEB' }}>
                <td className="px-4 py-3 text-sm text-mute">17 Apr</td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">H. Zouari</td>
                <td className="px-4 py-3 text-sm text-mute">Pharm. Gabès-C</td>
                <td className="px-4 py-3"><Pill variant="bad" text="Inflated+" /></td>
                <td className="px-4 py-3"><Pill variant="bad" text="0.94" /></td>
                <td className="px-4 py-3 text-xs text-mute">Positive but prior 3 visits negative</td>
                <td className="px-4 py-3"><Chip variant="bad" text="Investigate" /></td>
              </tr>
              <tr className="border-b border-line hover:bg-brand-soft" style={{ backgroundColor: '#FCEBEB' }}>
                <td className="px-4 py-3 text-sm text-mute">16 Apr</td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">N. Ayari</td>
                <td className="px-4 py-3 text-sm text-mute">Pharm. Médenine-S</td>
                <td className="px-4 py-3"><Pill variant="bad" text="Duplicate" /></td>
                <td className="px-4 py-3"><Pill variant="bad" text="0.91" /></td>
                <td className="px-4 py-3 text-xs text-mute">Identical text to 3 reports same day</td>
                <td className="px-4 py-3"><Chip variant="bad" text="Reject" /></td>
              </tr>
              <tr className="border-b border-line hover:bg-brand-soft">
                <td className="px-4 py-3 text-sm text-mute">15 Apr</td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">K. Tounsi</td>
                <td className="px-4 py-3 text-sm text-mute">Pharm. Kairouan-N</td>
                <td className="px-4 py-3"><Pill variant="warn" text="Contradiction" /></td>
                <td className="px-4 py-3"><Pill variant="warn" text="0.76" /></td>
                <td className="px-4 py-3 text-xs text-mute">Mouvement fort claimed, no order</td>
                <td className="px-4 py-3"><Chip variant="warn" text="Review" /></td>
              </tr>
              <tr className="border-b border-line hover:bg-brand-soft">
                <td className="px-4 py-3 text-sm text-mute">14 Apr</td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">L. Mansouri</td>
                <td className="px-4 py-3 text-sm text-mute">Pharm. Nabeul</td>
                <td className="px-4 py-3"><Pill variant="warn" text="Contradiction" /></td>
                <td className="px-4 py-3"><Pill variant="warn" text="0.71" /></td>
                <td className="px-4 py-3 text-xs text-mute">Contradicts last 2 stock reports</td>
                <td className="px-4 py-3"><Chip variant="warn" text="Review" /></td>
              </tr>
              <tr className="hover:bg-brand-soft">
                <td className="px-4 py-3 text-sm text-mute">13 Apr</td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">S. Mejri</td>
                <td className="px-4 py-3 text-sm text-mute">Pharm. Bizerte-W</td>
                <td className="px-4 py-3"><Pill variant="warn" text="Sparse" /></td>
                <td className="px-4 py-3"><Pill variant="warn" text="0.68" /></td>
                <td className="px-4 py-3 text-xs text-mute">4 words only, no flags</td>
                <td className="px-4 py-3"><Chip variant="warn" text="Coaching" /></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
