import React from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, LineElement, BarElement, PointElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import { KpiCard } from '../components/KpiCard';
import { SentimentSample } from '../components/SentimentSample';

ChartJS.register(CategoryScale, LinearScale, LineElement, BarElement, PointElement, Title, Tooltip, Legend, Filler);

export const Sentiment: React.FC = () => {
  const kpis = [
    { label: 'Positive', value: '68%', delta: 4, barPercent: 68, barColor: 'bg-ok' },
    { label: 'Neutral', value: '22%', delta: 0, barPercent: 22, barColor: 'bg-brand' },
    { label: 'Negative', value: '10%', delta: 1, deltaType: 'warn' as const, barPercent: 10, barColor: 'bg-bad' },
    { label: 'Reports analyzed', value: '1,541', delta: 0, barPercent: 100, barColor: 'bg-info' },
  ];

  const sentimentTrendData = {
    labels: ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8', 'W9', 'W10', 'W11', 'W12'],
    datasets: [
      {
        label: 'Positive',
        data: [62, 63, 65, 66, 64, 67, 68, 70, 69, 71, 70, 68],
        borderColor: '#1D9E75',
        backgroundColor: 'rgba(29, 158, 117, 0.1)',
        fill: true,
        tension: 0.3,
      },
      {
        label: 'Neutral',
        data: [26, 25, 24, 23, 24, 22, 22, 20, 21, 20, 21, 22],
        borderColor: '#D3D1C7',
        backgroundColor: 'rgba(211, 209, 199, 0.1)',
        fill: true,
        tension: 0.3,
      },
      {
        label: 'Negative',
        data: [12, 12, 11, 11, 12, 11, 10, 10, 10, 9, 9, 10],
        borderColor: '#B8263E',
        backgroundColor: 'rgba(184, 38, 62, 0.1)',
        fill: true,
        tension: 0.3,
      },
    ],
  };

  const sentimentDistData = {
    labels: ['Anim 1', 'Anim 2', 'Anim 3', 'Anim 4', 'Anim 5', 'Anim 6', 'Anim 7', 'Anim 8', 'Anim 9', 'Anim 10'],
    datasets: [
      {
        label: 'Positive',
        data: [82, 78, 74, 65, 58, 52, 48, 44, 35, 22],
        backgroundColor: '#1D9E75',
        borderRadius: 4,
      },
      {
        label: 'Neutral',
        data: [12, 16, 18, 22, 28, 30, 34, 32, 30, 32],
        backgroundColor: '#D3D1C7',
        borderRadius: 4,
      },
      {
        label: 'Negative',
        data: [6, 6, 8, 13, 14, 18, 18, 24, 35, 46],
        backgroundColor: '#B8263E',
        borderRadius: 4,
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
      <h1 className="text-3xl font-bold text-ink mb-1">Sentiment Analysis</h1>
      <p className="text-mute text-sm mb-6">LLM-enriched comment classification</p>

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
          <h3 className="text-lg font-semibold text-ink mb-4">Sentiment trend · 12 weeks</h3>
          <div style={{ height: '260px' }}>
            <Line data={sentimentTrendData} options={chartOptions} />
          </div>
        </div>
        <div className="bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">Distribution per animation</h3>
          <div style={{ height: '260px' }}>
            <Bar data={sentimentDistData} options={chartOptions} />
          </div>
        </div>
      </div>

      {/* Sample Comments */}
      <div className="bg-card border border-line rounded-lg p-5">
        <h3 className="text-lg font-semibold text-ink mb-4">Sample classified comments</h3>
        <SentimentSample type="pos" quote="Formation γ-3 super bien reçue par les équipes, très profitable." meta="Formation γ-3 · Pharm 834" />
        <SentimentSample type="pos" quote="Kit vitrine très visible, CA produit B +22% sur la semaine." meta="Kit vitrine Q2 · Pharm 142" />
        <SentimentSample type="neu" quote="Webinaire correct, peu d'interaction, audience limitée." meta="Webinaire X · Pharm 516" />
        <SentimentSample type="neg" quote="Salon Sud mal organisé, peu de pharmacies venues." meta="Salon Sud · Pharm 721" />
        <SentimentSample type="neg" quote="Concours C inutile pour ma clientèle, zéro intérêt." meta="Concours tier C · Pharm 905" />
      </div>
    </div>
  );
};
