import { Avatar } from '../components/Avatar';
import { MiniBar } from '../components/MiniBar';
import { Pill } from '../components/Pill';
import { DelegateCard } from '../components/DelegateCard';
import { delegates as staticDelegates } from '../data/delegates';
import { useManagerData } from '../hooks/useManagerData';
import { qColor } from '../utils/colors';

function scoreToQTier(score: number): 'A' | 'B' | 'C' | 'D' {
  if (score >= 0.8) return 'A';
  if (score >= 0.6) return 'B';
  if (score >= 0.4) return 'C';
  return 'D';
}

export function Delegates() {
  const { delegates: apiDelegates, loading } = useManagerData(123);

  // Map API scorecards to table format, fallback to static
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

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-22 font-bold text-ink mb-1">
          {delegateList.length} Delegates · Team Roster
        </h1>
        {loading && <p className="text-xs text-mute">Loading live data…</p>}
      </div>

      {/* Table */}
      <div className="bg-card rounded-lg border border-line overflow-hidden mb-6">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-line bg-brand-soft">
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Delegate</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Zone</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">CA vs Obj</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Prime %</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Visit Q</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Anom %</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Flags</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Risk</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-ink">Trend</th>
              </tr>
            </thead>
            <tbody>
              {delegateList.map((d) => (
                <tr
                  key={d.init}
                  className="border-b border-line hover:bg-brand-soft transition-colors"
                  style={{ backgroundColor: d.risky ? '#FEF5F5' : undefined }}
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Avatar init={d.init} name={d.name} />
                      <span className="text-sm font-semibold text-ink">{d.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-mute">{d.zone}</td>
                  <td className="px-4 py-3">
                    <MiniBar percent={d.ca} color="bg-brand" />
                  </td>
                  <td className="px-4 py-3 text-sm font-semibold text-ink">{d.prime}%</td>
                  <td className="px-4 py-3">
                    <Pill variant={qColor(d.q) as any} text={d.q} />
                  </td>
                  <td className="px-4 py-3 text-sm text-mute">{d.anom}%</td>
                  <td className="px-4 py-3 text-sm font-semibold text-ink">{d.flags}</td>
                  <td className="px-4 py-3">
                    <Pill
                      variant={d.risk < 0.3 ? 'ok' : d.risk < 0.6 ? 'warn' : 'bad'}
                      text={`${(d.risk * 100).toFixed(0)}%`}
                    />
                  </td>
                  <td
                    className="px-4 py-3 text-sm font-semibold"
                    style={{ color: d.trend.includes('▲') ? 'var(--ok)' : d.trend.includes('▼▼') ? 'var(--bad)' : 'var(--warn)' }}
                  >
                    {d.trend}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cards Grid */}
      <div className="mb-6">
        <h2 className="text-13 font-semibold text-ink mb-3">Delegate Cards · Quick View</h2>
        <div className="grid grid-cols-3 gap-4">
          {delegateList.map((d) => (
            <DelegateCard key={d.init} {...d} />
          ))}
        </div>
      </div>
    </div>
  );
}
