type ChipVariant = 'ok' | 'warn' | 'bad' | 'info';

interface ChipProps {
  variant: ChipVariant;
  text: string;
}

export function Chip({ variant, text }: ChipProps) {
  const getStyles = () => {
    switch (variant) {
      case 'ok':
        return { bg: '#E8F8F3', text: '#1D9E75', border: '#1D9E75' };
      case 'warn':
        return { bg: '#FBF5EC', text: '#BA7517', border: '#BA7517' };
      case 'bad':
        return { bg: '#FCEBEB', text: '#B8263E', border: '#B8263E' };
      case 'info':
        return { bg: '#EFF5FB', text: '#378ADD', border: '#378ADD' };
      default:
        return { bg: '#EFF5FB', text: '#378ADD', border: '#378ADD' };
    }
  };

  const styles = getStyles();

  return (
    <span
      className="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold"
      style={{
        backgroundColor: styles.bg,
        color: styles.text,
        border: `1px solid ${styles.border}`,
      }}
    >
      {text}
    </span>
  );
}
