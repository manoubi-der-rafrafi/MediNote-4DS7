export interface Animation {
  id: number;
  name: string;
  type: 'Training' | 'Event' | 'PLV' | 'Digital' | 'Promo' | 'Contest';
  roi: number;
  budget: number;
  invested: number;
  movementFort: number;
  pStrong: number;
  verdict: 'Keep' | 'Watch' | 'Drop';
  sentiment: string;
}

const names = [
  'Formation γ-3', 'Journée cardio', 'Kit vitrine Q2', 'Webinaire X', 'Gratuités Ramadan', 'Concours tier C', 'Salon Sud', 'Cadeaux fin année',
  'Formation ρ-1', 'Forum diabète', 'PLV été', 'Newsletter', 'Gratuité β', 'Concours A', 'Salon Nord', 'Cadeaux Aïd',
  'Form. allergies', 'Journée neuro', 'Kit hiver', 'Campagne TV', 'Promo insuline', 'Concours B', 'Salon Centre', 'Gift pack',
  'Form. pédiatrie', 'Cycle ortho', 'PLV Ramadan', 'Email drip', 'Promo vitamines', 'Concours D', 'Salon Est', 'Welcome kit',
];

const types: Array<'Training' | 'Event' | 'PLV' | 'Digital' | 'Promo' | 'Contest'> = ['Training', 'Event', 'PLV', 'Digital', 'Promo', 'Contest'];

function seededRandom(seed: number): number {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

export const animData: Animation[] = names.map((name, i) => {
  const roi = Math.max(0.1, 4.5 - i * 0.13 + (i % 3 ? 0.2 : -0.3));
  const budget = 30 + ((i * 13) % 180);
  const invested = Math.round(budget * (0.15 + seededRandom(i) * 0.7));
  const movementFort = Math.max(0, Math.min(100, Math.round(roi * 22)));
  const pStrong = Math.max(0, Math.min(1, roi / 4.5));
  
  let verdict: 'Keep' | 'Watch' | 'Drop';
  if (roi > 2.5) verdict = 'Keep';
  else if (roi > 1.5) verdict = 'Watch';
  else verdict = 'Drop';

  let sentiment: string;
  if (roi > 2) sentiment = `+${60 + Math.round(roi * 5)}%`;
  else if (roi > 1) sentiment = `+${30 + Math.round(roi * 8)}%`;
  else sentiment = `-${20 + Math.round((1.5 - roi) * 20)}%`;

  return {
    id: i,
    name,
    type: types[i % types.length],
    roi: parseFloat(roi.toFixed(2)),
    budget,
    invested,
    movementFort,
    pStrong: parseFloat(pStrong.toFixed(2)),
    verdict,
    sentiment,
  };
});
