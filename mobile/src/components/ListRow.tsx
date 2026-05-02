import React from 'react';

interface ListRowProps {
  icon?: React.ReactNode;
  title: string;
  subtitle?: string;
  rightElement?: React.ReactNode;
  bottomElement?: React.ReactNode;
}

export const ListRow: React.FC<ListRowProps> = ({ icon, title, subtitle, rightElement, bottomElement }) => {
  return (
    <div
      className="flex items-center gap-2.5 p-2.5 mb-2"
      style={{
        backgroundColor: 'var(--card)',
        border: '0.5px solid var(--border)',
        borderRadius: '12px',
      }}
    >
      {icon && <div className="flex-shrink-0">{icon}</div>}
      <div className="flex-1 min-w-0">
        <p className="text-[12.5px] font-medium text-[var(--text)] truncate">{title}</p>
        {subtitle && <p className="text-[10.5px] text-[var(--muted)] mt-0.5">{subtitle}</p>}
        {bottomElement}
      </div>
      {rightElement && <div className="flex-shrink-0">{rightElement}</div>}
    </div>
  );
};
