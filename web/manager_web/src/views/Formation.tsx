import { useState, useEffect } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { KpiCard } from '../components/KpiCard';
import { Pill } from '../components/Pill';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export function Formation() {
  const [chartsInit, setChartsInit] = useState(false);

  useEffect(() => {
    setChartsInit(true);
  }, []);

  // CA growth by formation count
  const growthData = {
    labels: ['No form.', '1', '2', '3+'],
    datasets: [
      {
        label: 'CA Growth %',
        data: [-2.1, 4.6, 9.8, 14.2],
        backgroundColor: ['#B8263E', '#BA7517', '#378ADD', '#1D9E75'],
        borderRadius: 4,
      },
    ],
  };

  const growthOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom' as const, boxWidth: 10 },
      title: { display: true, text: 'CA Growth by Formation Count' },
    },
    scales: {
      y: { title: { display: true, text: 'CA Growth %' }, grid: { color: '#E5E4DE' } },
    },
  };

  // Completion chart
  const completionData = {
    labels: ['AK', 'SB', 'IH', 'MG', 'FJ', 'RB', 'YM', 'AH', 'MD', 'SM', 'LM', 'KT', 'WB', 'TK', 'RD', 'AB', 'NA', 'HZ'],
    datasets: [
      {
        label: 'Formations Completed',
        data: [6, 5, 5, 4, 4, 3, 3, 3, 3, 2, 2, 1, 1, 1, 1, 0, 0, 0],
        backgroundColor: '#BA7517',
        borderRadius: 4,
      },
    ],
  };

  const completionOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom' as const, boxWidth: 10 },
      title: { display: true, text: 'Formation Completion per Delegate' },
    },
    scales: {
      y: { title: { display: true, text: 'Count' }, grid: { color: '#E5E4DE' } },
    },
  };

  if (!chartsInit) return <div>Loading...</div>;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-22 font-bold text-ink mb-1">Formation ROI</h1>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard
          label="Trained Delegates"
          value="11/18"
          delta={0}
          deltaType="neutral"
          barPercent={61}
          barColor="bg-brand"
        />
        <KpiCard
          label="Avg CA Lift"
          value="+14.2%"
          delta={0}
          deltaType="up"
          barPercent={72}
          barColor="bg-ok"
        />
        <KpiCard
          label="Visit Quality Lift"
          value="+18%"
          delta={0}
          deltaType="up"
          barPercent={70}
          barColor="bg-ok"
        />
        <KpiCard
          label="Formation Cost"
          value="18K DT"
          delta={0}
          deltaType="neutral"
          barPercent={9}
          barColor="bg-brand"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-card rounded-lg p-4 border border-line" style={{ height: 300 }}>
          <Bar data={growthData} options={growthOptions} />
        </div>
        <div className="bg-card rounded-lg p-4 border border-line" style={{ height: 300 }}>
          <Bar data={completionData} options={completionOptions} />
        </div>
      </div>

      {/* Table */}
      <div className="bg-card rounded-lg border border-line overflow-hidden">
        <div className="p-4 border-b border-line bg-brand-soft">
          <h2 className="text-13 font-semibold text-ink">Upcoming Formation Sessions</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-line">
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Date</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Program</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Duration</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Enrolled</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Capacity</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">ROI Expected</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-line hover:bg-brand-soft">
                <td className="px-4 py-3 text-sm text-mute">28 Apr</td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">Formation γ-3 · Cardio</td>
                <td className="px-4 py-3 text-sm text-mute">2 days</td>
                <td className="px-4 py-3 text-sm text-ink">8</td>
                <td className="px-4 py-3 text-sm text-ink">12</td>
                <td className="px-4 py-3"><Pill variant="ok" text="High ROI" /></td>
              </tr>
              <tr className="border-b border-line hover:bg-brand-soft">
                <td className="px-4 py-3 text-sm text-mute">05 May</td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">Journée scientifique diabète</td>
                <td className="px-4 py-3 text-sm text-mute">1 day</td>
                <td className="px-4 py-3 text-sm text-ink">5</td>
                <td className="px-4 py-3 text-sm text-ink">10</td>
                <td className="px-4 py-3"><Pill variant="ok" text="High ROI" /></td>
              </tr>
              <tr className="border-b border-line hover:bg-brand-soft">
                <td className="px-4 py-3 text-sm text-mute">12 May</td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">Formation ρ-1 · Neuro</td>
                <td className="px-4 py-3 text-sm text-mute">3 days</td>
                <td className="px-4 py-3 text-sm text-ink">3</td>
                <td className="px-4 py-3 text-sm text-ink">8</td>
                <td className="px-4 py-3"><Pill variant="info" text="Medium" /></td>
              </tr>
              <tr className="border-b border-line hover:bg-brand-soft">
                <td className="px-4 py-3 text-sm text-mute">19 May</td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">Atelier conseil client</td>
                <td className="px-4 py-3 text-sm text-mute">1 day</td>
                <td className="px-4 py-3 text-sm text-ink">11</td>
                <td className="px-4 py-3 text-sm text-ink">15</td>
                <td className="px-4 py-3"><Pill variant="ok" text="High ROI" /></td>
              </tr>
              <tr className="hover:bg-brand-soft">
                <td className="px-4 py-3 text-sm text-mute">26 May</td>
                <td className="px-4 py-3 text-sm font-semibold text-ink">Formation produit X</td>
                <td className="px-4 py-3 text-sm text-mute">2 days</td>
                <td className="px-4 py-3 text-sm text-ink">2</td>
                <td className="px-4 py-3 text-sm text-ink">8</td>
                <td className="px-4 py-3"><Pill variant="warn" text="Low Demand" /></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
