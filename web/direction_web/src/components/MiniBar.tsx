

interface MiniBarProps {
  percent: number;
  color?: string;
}

export function MiniBar({ percent, color = 'bg-info' }: MiniBarProps) {
  return (
    <div className="inline-block w-24 h-1.5 bg-line rounded-full overflow-hidden align-middle">
      <div
        className={`h-full ${color}`}
        style={{ width: `${Math.min(percent, 100)}%` }}
      />
    </div>
  );
}
