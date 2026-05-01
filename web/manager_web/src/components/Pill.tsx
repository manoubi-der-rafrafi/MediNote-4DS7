type PillVariant = 'ok' | 'warn' | 'bad' | 'info';

interface PillProps {
  variant: PillVariant;
  text: string;
}

export function Pill({ variant, text }: PillProps) {
  const getBgColor = (): string => {
    switch (variant) {
      case 'ok': return 'bg-ok';
      case 'warn': return 'bg-warn';
      case 'bad': return 'bg-bad';
      case 'info': return 'bg-info';
      default: return 'bg-info';
    }
  };

  return (
    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-semibold text-white ${getBgColor()}`}>
      {text}
    </span>
  );
}
