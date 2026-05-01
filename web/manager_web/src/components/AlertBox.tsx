interface AlertBoxProps {
  message: string;
}

export function AlertBox({ message }: AlertBoxProps) {
  return (
    <div
      className="p-4 rounded-lg border-l-4"
      style={{
        borderLeftColor: 'var(--bad)',
        backgroundColor: '#FCEBEB',
      }}
    >
      <p className="text-sm text-ink">{message}</p>
    </div>
  );
}
