import React from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';
import { KpiCard } from '../components/KpiCard';

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend, Filler);

export const Themes: React.FC = () => {
  const kpis = [
    { label: 'Themes tracked', value: '16', delta: 0, barPercent: 100, barColor: 'bg-brand' },
    { label: 'Total mentions', value: '2,184', delta: 15, barPercent: 90, barColor: 'bg-brand' },
    { label: 'Concurrence ▲', value: '+28%', delta: 28, deltaType: 'warn' as const, barPercent: 72, barColor: 'bg-warn' },
    { label: 'Rupture stock', value: '132', delta: -8, barPercent: 44, barColor: 'bg-bad' },
  ];

  const themeFreqData = {
    labels: ['stock', 'conseil', 'concurrence', 'emplacement', 'formation', 'prix', 'rupture', 'eff. indésirable', 'alerte', 'promotion', 'délai', 'emballage', 'dosage', 'marque', 'visibilité', 'retour'],
    datasets: [{
      label: 'Mentions',
      data: [312, 287, 241, 198, 176, 154, 132, 44, 89, 78, 67, 55, 48, 41, 38, 29],
      backgroundColor: '#D4537E',
      borderRadius: 4,
    }],
  };

  const themeEvolutionData = {
    labels: ['Q1\'24', 'Q2\'24', 'Q3\'24', 'Q4\'24', 'Q1\'25', 'Q2\'25', 'Q3\'25', 'Q4\'25', 'Q1\'26'],
    datasets: [
      {
        label: 'stock',
        data: [245, 260, 258, 270, 280, 285, 298, 305, 312],
        borderColor: '#D4537E',
        tension: 0.3,
      },
      {
        label: 'concurrence',
        data: [128, 142, 158, 176, 188, 195, 210, 225, 241],
        borderColor: '#7F77DD',
        tension: 0.3,
      },
      {
        label: 'conseil',
        data: [292, 288, 286, 280, 275, 278, 282, 285, 287],
        borderColor: '#1D9E75',
        tension: 0.3,
      },
      {
        label: 'rupture',
        data: [178, 172, 165, 158, 152, 148, 142, 138, 132],
        borderColor: '#BA7517',
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
      <h1 className="text-3xl font-bold text-ink mb-1">Themes</h1>
      <p className="text-mute text-sm mb-6">Semantic analysis of customer feedback</p>

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
          <h3 className="text-lg font-semibold text-ink mb-4">Themes frequency</h3>
          <div style={{ height: '360px' }}>
            <Bar data={themeFreqData} options={{ ...chartOptions, indexAxis: 'y' as const }} />
          </div>
        </div>

        <div className="bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">Theme evolution</h3>
          <div style={{ height: '360px' }}>
            <Line data={themeEvolutionData} options={chartOptions} />
          </div>
        </div>
      </div>
    </div>
  );
};
