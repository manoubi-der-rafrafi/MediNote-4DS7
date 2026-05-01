import { useState, useEffect } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { KpiCard } from '../components/KpiCard';
import { AnimCard } from '../components/AnimCard';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export function SemanticFlags() {
  const [chartsInit, setChartsInit] = useState(false);

  useEffect(() => {
    setChartsInit(true);
  }, []);

  const flagLabels = ['concurrence', 'rupture', 'emplacement', 'conseil', 'prix', 'formation', 'alerte', 'stock', 'délai', 'promo', 'dosage', 'retour', 'visibilité', 'marque', 'emballage', 'eff. indés.'];
  const flagData = [84, 62, 51, 38, 29, 22, 14, 12, 10, 8, 6, 5, 4, 3, 3, 3];

  const horizontalData = {
    labels: flagLabels,
    datasets: [
      {
        label: 'Count',
        data: flagData,
        backgroundColor: '#BA7517',
        borderRadius: 4,
      },
    ],
  };

  const horizontalOptions = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y' as const,
    plugins: {
      legend: { position: 'bottom' as const, boxWidth: 10 },
      title: { display: true, text: 'All 16 Flags — Team-Wide' },
    },
    scales: {
      x: { grid: { color: '#E5E4DE' } },
    },
  };

  // Heatmap data
  const delegateInits = ['AK', 'SB', 'MG', 'KT', 'NA', 'HZ'];
  const heatmapData = {
    labels: delegateInits,
    datasets: [
      {
        label: 'Concurrence',
        data: [4, 6, 8, 14, 16, 18],
        backgroundColor: '#BA7517',
      },
      {
        label: 'Rupture',
        data: [2, 2, 4, 6, 8, 10],
        backgroundColor: '#B8263E',
      },
      {
        label: 'Conseil',
        data: [10, 8, 6, 4, 2, 2],
        backgroundColor: '#1D9E75',
      },
      {
        label: 'Prix',
        data: [2, 1, 3, 5, 8, 12],
        backgroundColor: '#7F77DD',
      },
    ],
  };

  const heatmapOptions = {
    responsive: true,
    maintainAspectRatio: false,
    stacked: true,
    plugins: {
      legend: { position: 'bottom' as const, boxWidth: 10 },
      title: { display: true, text: 'Flag × Delegate Heatmap' },
    },
    scales: {
      y: { stacked: true, grid: { color: '#E5E4DE' } },
      x: { stacked: true, grid: { display: false } },
    },
  };

  if (!chartsInit) return <div>Loading...</div>;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-22 font-bold text-ink mb-1">Semantic Flags</h1>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard
          label="Top Flag: Concurrence"
          value="84"
          delta={-28}
          deltaType="down"
          barPercent={84}
          barColor="bg-bad"
        />
        <KpiCard
          label="Rupture Stock"
          value="62"
          delta={0}
          deltaType="warn"
          barPercent={62}
          barColor="bg-warn"
        />
        <KpiCard
          label="Eff. Indésirable"
          value="3"
          delta={0}
          deltaType="down"
          barPercent={3}
          barColor="bg-bad"
        />
        <KpiCard
          label="Total Mentions"
          value="2,184"
          delta={0}
          deltaType="neutral"
          barPercent={90}
          barColor="bg-brand"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-card rounded-lg p-4 border border-line" style={{ height: 400 }}>
          <Bar data={horizontalData} options={horizontalOptions} />
        </div>
        <div className="bg-card rounded-lg p-4 border border-line" style={{ height: 300 }}>
          <Bar data={heatmapData} options={heatmapOptions} />
        </div>
      </div>

      {/* Concurrence Details */}
      <div className="mb-6">
        <h2 className="text-13 font-semibold text-ink mb-3">Concurrence Mentions · Details</h2>
        <div className="space-y-3">
          <AnimCard
            delegateName="K. Tounsi"
            date="16 Apr"
            pharmacy="Pharm. Kairouan-N"
            body="Concurrent laboratoire Y présente une offre 15% moins chère, pharmacie hésite à commander."
            tags={[
              { text: 'concurrence', variant: 'warn' },
              { text: 'prix', variant: 'bad' },
            ]}
          />
          <AnimCard
            delegateName="L. Mansouri"
            date="15 Apr"
            pharmacy="Pharm. Nabeul"
            body="Concurrence mentionne reprise des invendus, nous devrions proposer même option."
            tags={[
              { text: 'concurrence', variant: 'warn' },
              { text: 'stock', variant: 'bad' },
            ]}
          />
          <AnimCard
            delegateName="S. Mejri"
            date="12 Apr"
            pharmacy="Pharm. Bizerte-W"
            body="Visite concurrent 2 jours avant, a placé son kit vitrine."
            tags={[
              { text: 'concurrence', variant: 'warn' },
              { text: 'emplacement', variant: 'bad' },
            ]}
          />
        </div>
      </div>
    </div>
  );
}
