import React from 'react';
import { Pill } from './Pill';

interface ApproveRowProps {
  name: string;
  meta: string;
  score: number;
  scoreClass: 'ok' | 'info' | 'warn' | 'bad';
  onApprove: () => void;
  onReject: () => void;
  approved?: boolean;
  rejected?: boolean;
}

export const ApproveRow: React.FC<ApproveRowProps> = ({
  name,
  meta,
  score,
  scoreClass,
  onApprove,
  onReject,
  approved = false,
  rejected = false,
}) => {
  const opacity = approved || rejected ? 'opacity-40' : 'opacity-100';

  return (
    <div className={`flex items-center justify-between p-3 border-b border-line ${opacity}`}>
      <div>
        <div className="font-semibold text-ink">{name}</div>
        <div className="text-xs text-mute">{meta}</div>
      </div>
      <div className="flex items-center gap-3">
        <Pill variant={scoreClass} text={approved ? 'Approved ✓' : rejected ? 'Rejected ✗' : score.toFixed(2)} />
        <button
          onClick={onApprove}
          disabled={approved || rejected}
          className="px-3 py-1 bg-ok text-white rounded text-xs font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Approve
        </button>
        <button
          onClick={onReject}
          disabled={approved || rejected}
          className="px-3 py-1 bg-bad text-white rounded text-xs font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Reject
        </button>
      </div>
    </div>
  );
};
