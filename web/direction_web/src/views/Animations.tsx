import { useMemo } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { KpiCard } from '../components/KpiCard';
import { AnimationTable } from '../components/AnimationTable';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function AnimationsDashboard() {
  const kpis = [
    { label: 'Active animations', value: '32', delta: 12, barPercent: 32, barColor: 'bg-ok' },
    { label: 'Budget invested', value: '1.8M DT', delta: -35.3, deltaType: 'down' as const, barPercent: 64.3, barColor: 'bg-warn' },
    { label: 'Avg ROI', value: '2.1×', delta: 18.5, barPercent: 42, barColor: 'bg-ok' },
    { label: 'P(strong) avg', value: '0.62', delta: 5.2, barPercent: 62, barColor: 'bg-ok' },
  ];

  // Generate 32 animations with realistic data
  const animationRows = useMemo(() => {
    const rows = [];
    for (let i = 1; i <= 32; i++) {
      const roi = 0.8 + Math.random() * 3.2;
      rows.push({
        id: i,
        code: `ANI${String(i).padStart(3, '0')}`,
        name: `Animation ${i}`,
        roi,
        budget: `${Math.floor(Math.random() * 150) + 50}K`,
        invested: `${Math.floor(Math.random() * 120) + 20}K`,
        mouvementFort: Math.floor(Math.random() * 100),
        pStrong: 0.3 + Math.random() * 0.7,
        verdict: roi > 2.0 ? 'strong' : roi > 1.2 ? 'pending' : 'weak' as 'strong' | 'weak' | 'pending',
      });
    }
    return rows;
  }, []);

  // ROI ranking (first 16)
  const roiRankingData = {
    labels: animationRows.slice(0, 16).map((r) => r.code),
    datasets: [{
      label: 'ROI',
      data: animationRows.slice(0, 16).map((r) => r.roi),
      backgroundColor: (ctx: any) => {
        const value = ctx.parsed.y;
        if (value >= 2.5) return '#1D9E75';
        if (value >= 1.5) return '#378ADD';
        if (value >= 1) return '#BA7517';
        return '#B8263E';
      },
      borderRadius: 4,
    }],
  };

  // Budget by type
  const budgetByTypeData = {
    labels: ['Training', 'Event', 'PLV', 'Digital', 'Promo', 'Contest'],
    datasets: [
      {
        label: 'Requested',
        data: [320, 280, 250, 180, 410, 160],
        backgroundColor: '#E5E4DE',
        borderRadius: 4,
      },
      {
        label: 'Invested',
        data: [220, 150, 180, 80, 280, 90],
        backgroundColor: '#378ADD',
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
      <h1 className="text-3xl font-bold text-ink mb-1">Animations</h1>
      <p className="text-mute text-sm mb-6">Campaign performance and ROI tracking</p>

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
          <h3 className="text-lg font-semibold text-ink mb-4">ROI ranking (top 16)</h3>
          <div style={{ height: '260px' }}>
            <Bar data={roiRankingData} options={chartOptions} />
          </div>
        </div>
        <div className="bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">Budget by type</h3>
          <div style={{ height: '260px' }}>
            <Bar data={budgetByTypeData} options={chartOptions} />
          </div>
        </div>
      </div>

      {/* Animation Table */}
      <AnimationTable rows={animationRows} />
    </div>
  );
}
