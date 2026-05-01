import { useEffect, useState } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, PointElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { Scatter, Doughnut, Bar } from 'react-chartjs-2';
import { KpiCard } from '../components/KpiCard';
import { AlertBox } from '../components/AlertBox';
import { CoachCard } from '../components/CoachCard';
import { FlagTile } from '../components/FlagTile';
import { delegates as staticDelegates } from '../data/delegates';
import { coachingQueue as staticCoachingQueue } from '../data/coaching';
import { useManagerData } from '../hooks/useManagerData';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, PointElement, Title, Tooltip, Legend, Filler);

function scoreToQTier(score: number): 'A' | 'B' | 'C' | 'D' {
  if (score >= 0.8) return 'A';
  if (score >= 0.6) return 'B';
  if (score >= 0.4) return 'C';
  return 'D';
}

export function Dashboard() {
  const [chartsInit, setChartsInit] = useState(false);
  const [period, setPeriod] = useState<'MTD'|'QTD'|'YTD'>('QTD');
  const { delegates: apiDelegates, performanceMetrics, delegateCoaching, riskSynthesis, loading } = useManagerData(123);

  useEffect(() => { setChartsInit(true); }, []);

  const perf = performanceMetrics as any;

  // KPIs — real API data with static fallbacks
  const teamCA          = perf?.avg_team_score != null ? +(perf.avg_team_score * 100).toFixed(1) : 87.4;
  const teamPrime       = perf?.predictions?.overall_risk_score_pct != null
    ? +(100 - perf.predictions.overall_risk_score_pct * 100).toFixed(1)
    : 58.1;
  const atRiskCount     = perf?.predictions?.delegates_at_risk_missing_target?.count ?? 3;
  const needCoaching    = perf?.predictions?.delegates_with_churn_risk?.count ?? 5;
  const suspiciousReports = perf?.anomaly_rate_pct ?? 6.2;

  // Delegate list — map API scorecards or fallback to static
  const apiCards = Array.isArray(apiDelegates) && apiDelegates.length > 0 ? apiDelegates : null;
  const delegateList = apiCards
    ? apiCards.map((d: any) => ({
        init:  (d.id_delegate || 'NN').slice(0, 2).toUpperCase(),
        name:  d.delegate_name || d.id_delegate || 'Delegate',
        zone:  d.zone || d.gouvernorat || '—',
        ca:    +(d.ca_achievement_pct ?? 0).toFixed(1),
        prime: +(d.score_normalized != null ? d.score_normalized * 100 : 0).toFixed(1),
        q:     scoreToQTier(d.score_normalized ?? 0),
        anom:  d.anomaly_rate ?? 0,
        flags: d.flag_count ?? 0,
        risk:  +(1 - (d.score_normalized ?? 0)).toFixed(2),
        trend: d.trend || '—',
        risky: (d.ca_achievement_pct ?? 0) < 55,
      }))
    : staticDelegates;

  // Coaching queue — map API coaching or fallback
  const coachingList = Array.isArray(delegateCoaching) && delegateCoaching.length > 0
    ? delegateCoaching.slice(0, 5).map((c: any, i: number) => ({
        init:    (c.delegate_id || `D${i}`).slice(0, 2).toUpperCase(),
        name:    c.delegate_id || `Delegate ${i + 1}`,
        risk:    c.gaps?.length > 2 ? 0.85 : c.gaps?.length > 0 ? 0.6 : 0.4,
        reasons: (c.coaching_tips || []).slice(0, 2).join(' · ') || 'See report',
        cta:     c.gaps?.length > 2 ? 'Urgent 1:1' : 'Schedule review',
      }))
    : staticCoachingQueue;

  // Semantic flags from risk synthesis components or fallback
  const flags = (riskSynthesis as any)?.components?.semantic_flags || null;

  // Bubble chart datasets split by CA tier
  const bubbleData = {
    labels: ['Delegate Clustering'],
    datasets: [
      {
        label: 'High (CA ≥ 100%)',
        data: delegateList.filter(d => d.ca >= 100).map(d => ({ x: d.ca, y: d.prime, r: 8 + d.prime / 12 })),
        backgroundColor: 'rgba(29, 158, 117, 0.55)',
        borderColor: 'rgba(29, 158, 117, 0.8)',
      },
      {
        label: 'Medium (CA 75-99%)',
        data: delegateList.filter(d => d.ca >= 75 && d.ca < 100).map(d => ({ x: d.ca, y: d.prime, r: 6 + d.prime / 14 })),
        backgroundColor: 'rgba(55, 138, 221, 0.5)',
        borderColor: 'rgba(55, 138, 221, 0.8)',
      },
      {
        label: 'At risk (CA 55-74%)',
        data: delegateList.filter(d => d.ca >= 55 && d.ca < 75).map(d => ({ x: d.ca, y: d.prime, r: 5 + d.prime / 16 })),
        backgroundColor: 'rgba(186, 117, 23, 0.6)',
        borderColor: 'rgba(186, 117, 23, 0.8)',
      },
      {
        label: 'Critical (CA < 55%)',
        data: delegateList.filter(d => d.ca < 55).map(d => ({ x: d.ca, y: d.prime, r: 4 + d.prime / 18 })),
        backgroundColor: 'rgba(184, 38, 62, 0.7)',
        borderColor: 'rgba(184, 38, 62, 0.9)',
      },
    ],
  };

  const bubbleOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom' as const, boxWidth: 10 },
      title: { display: true, text: 'Delegate Clustering — CA vs Objectif × Visit Quality' },
    },
    scales: {
      x: { title: { display: true, text: 'CA vs Objectif (%)' }, min: 30, max: 120, grid: { color: '#E5E4DE', drawBorder: false } },
      y: { title: { display: true, text: 'Prime %' }, min: 0, max: 100, grid: { color: '#E5E4DE', drawBorder: false } },
    },
  };

  const qualityData = {
    labels: ['A', 'B', 'C', 'D'],
    datasets: [{
      data: [
        delegateList.filter(d => d.q === 'A').length || 3,
        delegateList.filter(d => d.q === 'B').length || 6,
        delegateList.filter(d => d.q === 'C').length || 6,
        delegateList.filter(d => d.q === 'D').length || 3,
      ],
      backgroundColor: ['#1D9E75', '#378ADD', '#BA7517', '#B8263E'],
    }],
  };

  const qualityOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom' as const, boxWidth: 10 },
      title: { display: true, text: 'Visit Quality Distribution' },
    },
    cutout: '62%',
  };

  const formationData = {
    labels: ['No form.', '1', '2', '3+'],
    datasets: [{
      label: 'CA Growth %',
      data: [-2.1, 4.6, 9.8, 14.2],
      backgroundColor: ['#B8263E', '#BA7517', '#BA7517', '#1D9E75'],
      borderRadius: 4,
    }],
  };

  const formationOptions = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y' as const,
    plugins: {
      legend: { position: 'bottom' as const, boxWidth: 10 },
      title: { display: true, text: 'Formation ROI — Trained vs Untrained' },
    },
    scales: { x: { title: { display: true, text: 'CA Growth %' }, grid: { color: '#E5E4DE' } } },
  };

  if (!chartsInit) return <div>Loading...</div>;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-22 font-bold text-ink mb-1">Team performance — Karim Belhadj</h1>
        <p className="text-xs text-mute">
          {delegateList.length} delegates · 9 zones · Grand Tunis + Nord ·{' '}
          {loading ? 'Loading…' : 'Live data'}
        </p>
        <div className="flex gap-2 mt-3">
          {['MTD', 'QTD', 'YTD'].map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p as 'MTD'|'QTD'|'YTD')}
              className={`px-3 py-1 rounded text-xs font-semibold transition-all ${period === p ? 'text-white' : 'text-mute'}`}
              style={{ backgroundColor: period === p ? 'var(--brand)' : 'transparent' }}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="Team CA vs Obj"     value={`${teamCA}%`}            delta={-12.6} deltaType="warn" barPercent={teamCA}           barColor="bg-warn" />
        <KpiCard label="Prime Realization"  value={`${teamPrime}%`}         delta={4.7}   deltaType="up"   barPercent={teamPrime}         barColor="bg-brand" />
        <KpiCard label="Suspicious Reports" value={`${suspiciousReports}%`} delta={-1.1}  deltaType="up"   barPercent={suspiciousReports} barColor="bg-warn" />
        <KpiCard label="Need Coaching"      value={`${needCoaching}`}       delta={atRiskCount - needCoaching} deltaType="warn" barPercent={Math.round(needCoaching / Math.max(delegateList.length, 1) * 100)} barColor="bg-bad" />
      </div>

      {/* Alert */}
      <div className="mb-6">
        <AlertBox message={`${atRiskCount} delegates at high attrition risk — composite trend has declined 3 months. Schedule 1:1 this week.`} />
      </div>

      {/* Charts row 1: Bubble + Coaching */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="col-span-2 bg-card rounded-lg p-4 border border-line" style={{ height: 300 }}>
          <h3 className="text-sm font-semibold text-ink mb-2">Delegate Clustering <span className="text-xs text-mute ml-2">{period}</span></h3>
          <Scatter data={bubbleData} options={bubbleOptions} />
        </div>
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-ink">Coaching Priority · Top 5 <span className="text-xs text-mute ml-2">{period}</span></h3>
          {coachingList.map((item: any) => (
            <CoachCard key={item.init} {...item} />
          ))}
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-card rounded-lg p-4 border border-line" style={{ height: 300 }}>
          <h3 className="text-sm font-semibold text-ink mb-2">Visit Quality Distribution <span className="text-xs text-mute ml-2">{period}</span></h3>
          <Doughnut data={qualityData} options={qualityOptions} />
        </div>

        <div className="bg-card rounded-lg p-4 border border-line">
          <h3 className="text-sm font-semibold text-ink mb-3">Semantic Flags Triggered</h3>
          <div className="grid grid-cols-2 gap-2">
            <FlagTile number={flags?.concurrence ?? 84} label="Concurrence" />
            <FlagTile number={flags?.rupture ?? 62}     label="Rupture" />
            <FlagTile number={flags?.emplacement ?? 51} label="Emplacement" />
            <FlagTile number={flags?.conseil ?? 38}     label="Conseil" />
            <FlagTile number={flags?.prix ?? 29}        label="Prix" />
            <FlagTile number={flags?.formation ?? 22}   label="Formation" />
            <FlagTile number={flags?.alerte ?? 14}      label="Alerte" />
            <FlagTile number={flags?.indesirable ?? 3}  label="Eff. Indés." />
          </div>
        </div>

        <div className="bg-card rounded-lg p-4 border border-line" style={{ height: 300 }}>
          <h3 className="text-sm font-semibold text-ink mb-2">Formation ROI <span className="text-xs text-mute ml-2">{period}</span></h3>
          <Bar data={formationData} options={formationOptions} />
        </div>
      </div>
    </div>
  );
}
