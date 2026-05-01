import toast from 'react-hot-toast';

const SEVERITY_EMOJI = {
  CRITICAL: '🔴',
  URGENT: '🟠',
  WATCH: '🟡',
};

export interface Alert {
  id: string;
  severity: 'CRITICAL' | 'URGENT' | 'WATCH';
  message: string;
  timestamp: string;
}

export function connectAlerts(userId: number, onAlert?: (alert: Alert) => void) {
  const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
  const ws = new WebSocket(`${wsUrl}/ws/alerts/${userId}`);

  ws.onopen = () => {
    console.log('WebSocket connected');
  };

  ws.onmessage = (event) => {
    try {
      const alert: Alert = JSON.parse(event.data);
      const emoji = SEVERITY_EMOJI[alert.severity] || '🔔';
      
      toast(`${emoji} ${alert.message}`, {
        duration: 6000,
        position: 'top-right',
        style: {
          background: '#22222A',
          color: '#F4F4F6',
          border: '1px solid rgba(255,255,255,0.08)',
        },
      });

      onAlert?.(alert);
    } catch (err) {
      console.error('Failed to parse alert:', err);
    }
  };

  ws.onerror = (err) => {
    console.error('WebSocket error:', err);
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected');
  };

  return ws;
}
