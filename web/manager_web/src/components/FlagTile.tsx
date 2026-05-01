interface FlagTileProps {
  number: number;
  label: string;
}

export function FlagTile({ number, label }: FlagTileProps) {
  return (
    <div
      className="p-4 rounded-lg text-center"
      style={{ backgroundColor: 'var(--brand-soft)' }}
    >
      <div className="text-24 font-bold text-ink">{number}</div>
      <div className="text-xs uppercase font-semibold text-mute mt-1">{label}</div>
    </div>
  );
}
