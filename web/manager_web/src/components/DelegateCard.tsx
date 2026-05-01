import { Avatar } from './Avatar';
import { Pill } from './Pill';
import { MiniBar } from './MiniBar';
import { qColor, riskColor } from '../utils/colors';
import type { QualityTier } from '../data/delegates';

interface DelegateCardProps {
  init: string;
  name: string;
  zone: string;
  ca: number;
  prime: number;
  q: QualityTier;
  risk: number;
}

export function DelegateCard({ init, name, zone, ca, prime, q, risk }: DelegateCardProps) {
  return (
    <div
      className="p-4 rounded-lg border"
      style={{
        backgroundColor: 'var(--brand-soft)',
        borderColor: 'var(--line)',
      }}
    >
      <div className="flex items-center gap-2 mb-3">
        <Avatar init={init} name={name} />
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-ink truncate">{name}</h4>
          <p className="text-xs text-mute truncate">{zone}</p>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-mute">CA vs Obj</span>
          <MiniBar percent={ca} color="bg-brand" />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-mute">Prime %</span>
          <span className="text-sm font-semibold text-ink">{prime}%</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-mute">Visit Q</span>
          <Pill variant={qColor(q) as any} text={q} />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-mute">Risk</span>
          <Pill variant={riskColor(risk) as any} text={`${(risk * 100).toFixed(0)}%`} />
        </div>
      </div>
    </div>
  );
}
