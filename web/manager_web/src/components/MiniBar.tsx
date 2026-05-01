interface MiniBarProps {
  percent: number;
  color?: string;
}

export function MiniBar({ percent, color = 'bg-info' }: MiniBarProps) {
  return (
    <div className="h-1.5 w-24 bg-line rounded-full overflow-hidden">
      <div
        className={`h-full ${color} transition-all`}
        style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
      />
    </div>
  );
}
