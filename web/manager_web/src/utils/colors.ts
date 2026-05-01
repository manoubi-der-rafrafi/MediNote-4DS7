import type { QualityTier } from '../data/delegates';

export const qColor = (q: QualityTier): string => {
  switch (q) {
    case 'A': return 'pill-ok';
    case 'B': return 'pill-info';
    case 'C': return 'pill-warn';
    case 'D': return 'pill-bad';
    default: return 'pill-ok';
  }
};

export const caColor = (ca: number): string => {
  if (ca >= 100) return 'var(--ok)';
  if (ca >= 85) return 'var(--info)';
  if (ca >= 65) return 'var(--warn)';
  return 'var(--bad)';
};

export const riskColor = (risk: number): string => {
  if (risk < 0.3) return 'pill-ok';
  if (risk < 0.6) return 'pill-warn';
  return 'pill-bad';
};

export const trendColor = (trend: string): string => {
  if (trend.includes('▲')) return 'var(--ok)';
  if (trend.includes('▼▼')) return 'var(--bad)';
  if (trend.includes('▼')) return 'var(--warn)';
  return 'var(--mute)';
};

export const riskBgColor = (risk: number): string => {
  if (risk >= 0.8) return '#FCEBEB'; // red tint
  if (risk >= 0.6) return '#FBF5EC'; // orange tint (same as --bg)
  return '#F0F7FF'; // blue tint
};

export const riskBgBorder = (risk: number): string => {
  if (risk >= 0.8) return '#501313';
  if (risk >= 0.6) return '#BA7517';
  return '#378ADD';
};
