interface AlertBadgeProps {
  type: 'bad' | 'warn' | 'info';
  title: string;
  message: string;
}

export function AlertBadge({ type, title, message }: AlertBadgeProps) {
  const getColors = () => {
    switch (type) {
      case 'bad':
        return { border: 'border-l-4 border-bad', bg: 'bg-red-50' };
      case 'warn':
        return { border: 'border-l-4 border-warn', bg: 'bg-yellow-50' };
      case 'info':
        return { border: 'border-l-4 border-info', bg: 'bg-blue-50' };
    }
  };

  const { border, bg } = getColors();

  return (
    <div className={`${border} ${bg} rounded p-3 mb-2`}>
      <div className="font-medium text-ink text-sm">{title}</div>
      <div className="text-xs text-mute mt-1">{message}</div>
    </div>
  );
}
