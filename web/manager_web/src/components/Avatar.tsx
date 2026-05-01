interface AvatarProps {
  init: string;
  name?: string;
}

export function Avatar({ init, name }: AvatarProps) {
  return (
    <div
      className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 font-bold text-xs"
      style={{ backgroundColor: 'var(--brand-soft)', color: 'var(--brand-dark)' }}
      title={name}
    >
      {init}
    </div>
  );
}
