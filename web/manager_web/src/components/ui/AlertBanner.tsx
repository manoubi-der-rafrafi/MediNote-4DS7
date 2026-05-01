import React, { useState } from 'react';
import { X } from 'lucide-react';
import { Badge } from './Badge';

type AlertSeverity = 'CRITICAL' | 'URGENT' | 'WATCH';

interface AlertBannerProps {
  type: 'info' | 'success' | 'warning' | 'error';
  severity: AlertSeverity;
  message: string;
  cta?: { label: string; onClick: () => void };
  onDismiss?: () => void;
  dismissible?: boolean;
}

const severityConfig: Record<AlertSeverity, { bg: string; border: string; icon: string; badge: string }> = {
  CRITICAL: {
    bg: 'bg-red/10',
    border: 'border-red/30',
    icon: '🔴',
    badge: 'danger',
  },
  URGENT: {
    bg: 'bg-orange/10',
    border: 'border-orange/30',
    icon: '🟠',
    badge: 'warning',
  },
  WATCH: {
    bg: 'bg-gold/10',
    border: 'border-gold/30',
    icon: '🟡',
    badge: 'info',
  },
};

export const AlertBanner: React.FC<AlertBannerProps> = ({
  severity,
  message,
  cta,
  onDismiss,
  dismissible = true,
}) => {
  const [visible, setVisible] = useState(true);
  const config = severityConfig[severity];

  const handleDismiss = () => {
    setVisible(false);
    onDismiss?.();
  };

  if (!visible) return null;

  return (
    <div className={`${config.bg} border ${config.border} rounded-lg p-4 flex items-center justify-between gap-4`}>
      <div className="flex items-start gap-3 flex-1">
        <span className="text-xl">{config.icon}</span>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant={config.badge as any}>{severity}</Badge>
          </div>
          <p className="text-sm text-gray-200">{message}</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {cta && (
          <button
            onClick={cta.onClick}
            className="px-3 py-1.5 bg-manager text-white text-xs font-semibold rounded hover:opacity-90 transition-opacity"
          >
            {cta.label}
          </button>
        )}
        {dismissible && (
          <button
            onClick={handleDismiss}
            className="p-1 hover:bg-black/20 rounded transition-colors"
          >
            <X size={16} />
          </button>
        )}
      </div>
    </div>
  );
};
