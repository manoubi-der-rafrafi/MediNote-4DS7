import { useState } from 'react';

export function PrimeSimulator() {
  const [rate, setRate] = useState(50);

  const payout = ((rate / 100 * 143 * 14500) / 1000).toFixed(0);
  const baseline = 53.4;
  const incremental = rate - baseline;

  return (
    <div className="bg-card border border-line rounded-lg p-5">
      <h3 className="text-lg font-semibold text-ink mb-4">Prime Simulator</h3>

      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <label className="text-label">Prime rate</label>
          <span className="text-kpi">{rate}%</span>
        </div>
        <input
          type="range"
          min="30"
          max="100"
          value={rate}
          onChange={(e) => setRate(Number(e.target.value))}
          className="w-full h-2 bg-line rounded-lg appearance-none cursor-pointer"
          style={{
            background: `linear-gradient(to right, var(--ok) 0%, var(--ok) ${rate}%, #E5E4DE ${rate}%, #E5E4DE 100%)`,
          }}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="text-xs text-mute mb-1">Payout</div>
          <div className="text-xl font-bold text-ink">{payout}K DT</div>
        </div>
        <div>
          <div className="text-xs text-mute mb-1">vs Baseline 53.4%</div>
          <div className={`text-xl font-bold ${incremental >= 0 ? 'text-ok' : 'text-bad'}`}>
            {incremental > 0 ? '+' : ''}{incremental.toFixed(1)}%
          </div>
        </div>
      </div>
    </div>
  );
}
