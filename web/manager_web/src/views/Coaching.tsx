import { KpiCard } from '../components/KpiCard';
import { CoachCard } from '../components/CoachCard';
import { coachingQueue } from '../data/coaching';

export function Coaching() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-22 font-bold text-ink mb-1">Coaching Queue</h1>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard
          label="High Risk"
          value="3"
          delta={0}
          deltaType="warn"
          barPercent={17}
          barColor="bg-bad"
        />
        <KpiCard
          label="Medium Risk"
          value="2"
          delta={0}
          deltaType="warn"
          barPercent={11}
          barColor="bg-warn"
        />
        <KpiCard
          label="Scheduled 1:1"
          value="2/5"
          delta={0}
          deltaType="neutral"
          barPercent={40}
          barColor="bg-brand"
        />
        <KpiCard
          label="Avg Improvement"
          value="+11.3%"
          delta={0}
          deltaType="up"
          barPercent={56}
          barColor="bg-ok"
        />
      </div>

      {/* Full Coaching Queue */}
      <div className="bg-card rounded-lg p-6 border border-line">
        <h2 className="text-13 font-semibold text-ink mb-4">Full Coaching Queue</h2>
        <div className="space-y-3">
          {coachingQueue.map((item) => (
            <CoachCard key={item.init} {...item} />
          ))}
        </div>
      </div>
    </div>
  );
}
