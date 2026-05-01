import { Chip } from './Chip';

interface AnimCardProps {
  delegateName: string;
  date: string;
  pharmacy: string;
  body: string;
  tags: Array<{ text: string; variant: 'ok' | 'warn' | 'bad' | 'info' }>;
}

export function AnimCard({ delegateName, date, pharmacy, body, tags }: AnimCardProps) {
  return (
    <div className="p-4 bg-card rounded-lg border border-line">
      <div className="flex items-start justify-between mb-2">
        <div>
          <h4 className="text-sm font-semibold text-ink">{delegateName}</h4>
          <p className="text-xs text-mute">{date} · {pharmacy}</p>
        </div>
      </div>
      <p className="text-sm italic text-ink mb-3 leading-relaxed">"{body}"</p>
      <div className="flex flex-wrap gap-2">
        {tags.map((tag, idx) => (
          <Chip key={idx} variant={tag.variant} text={tag.text} />
        ))}
      </div>
    </div>
  );
}
