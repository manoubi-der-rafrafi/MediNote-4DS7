

interface PillProps {
  variant: 'ok' | 'warn' | 'bad' | 'info';
  text: string;
}

export function Pill({ variant, text }: PillProps) {
  const getColors = () => {
    switch (variant) {
      case 'ok':
        return 'bg-green-100 text-ok';
      case 'warn':
        return 'bg-yellow-100 text-warn';
      case 'bad':
        return 'bg-red-100 text-bad';
      case 'info':
        return 'bg-blue-100 text-info';
    }
  };

  return (
    <span className={`inline-block ${getColors()} px-2 py-1 rounded text-xs font-medium`}>
      {text}
    </span>
  );
}
