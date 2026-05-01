import { Avatar } from './Avatar';
import { Pill } from './Pill';
import { riskBgColor, riskBgBorder } from '../utils/colors';

interface CoachCardProps {
  init: string;
  name: string;
  risk: number;
  reasons: string;
  cta: string;
}

export function CoachCard({ init, name, risk, reasons, cta }: CoachCardProps) {
  const getRiskPill = (r: number): 'ok' | 'warn' | 'bad' => {
    if (r < 0.3) return 'ok';
    if (r < 0.6) return 'warn';
    return 'bad';
  };

  const bgColor = riskBgColor(risk);
  const borderColor = riskBgBorder(risk);

  return (
    <div
      className="p-4 rounded-lg border"
      style={{
        backgroundColor: bgColor,
        borderColor: borderColor,
      }}
    >
      <div className="flex items-start gap-3 mb-2">
        <Avatar init={init} name={name} />
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-ink">{name}</h3>
          <Pill variant={getRiskPill(risk)} text={`Risk ${(risk * 100).toFixed(0)}%`} />
        </div>
      </div>
      <p className="text-xs text-mute mb-3 leading-relaxed">{reasons}</p>
      <div className="text-xs font-semibold" style={{ color: borderColor }}>
        → {cta}
      </div>
    </div>
  );
}
