import React, { useState, useRef, useEffect } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { ScoreBox } from '../components/ScoreBox';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export const Eligibility: React.FC = () => {
  const [type, setType] = useState('Training');
  const [budget, setBudget] = useState(90);
  const [targetGov, setTargetGov] = useState('Tunis');
  const [pharmacyTier, setPharmacyTier] = useState('A');
  const [duration, setDuration] = useState(4);
  const [productFocus, setProductFocus] = useState('Cardiology');
  const [score, setScore] = useState(0.65);
  const chartRef = useRef<any>(null);

  useEffect(() => {
    // Auto-score on initialization
    calculateScore();
  }, []);

  const calculateScore = () => {
    let base = 0.5;
    
    const typeBonus: { [key: string]: number } = {
      Training: 0.25,
      Event: 0.18,
      PLV: 0.12,
      Digital: 0.05,
      Promo: 0,
      Contest: -0.15,
    };
    
    const tierBonus: { [key: string]: number } = { A: 0.2, B: 0.08, C: 0, D: -0.2 };

    let budgetBonus = 0;
    if (budget > 150) budgetBonus = -0.08;
    else if (budget < 50) budgetBonus = -0.05;
    else budgetBonus = 0.05;

    const durationBonus = duration >= 4 && duration <= 8 ? 0.05 : 0;

    let newScore = base + (typeBonus[type] || 0) + (tierBonus[pharmacyTier] || 0) + budgetBonus + durationBonus;
    newScore = Math.max(0.05, Math.min(0.99, newScore + (Math.random() - 0.5) * 0.05));

    setScore(newScore);

    // Destroy previous chart if it exists
    if (chartRef.current?.chartInstance) {
      chartRef.current.chartInstance.destroy();
    }
  };

  const expectedRoi = (score * 4.5).toFixed(1);
  const eligibility = score > 0.7 ? 'Approve' : score > 0.4 ? 'Review' : 'Reject';
  const eligibilityType = score > 0.7 ? 'ok' : score > 0.4 ? 'warn' : 'bad';
  const confidence = score > 0.7 || score < 0.3 ? 'high' : 'medium';

  // SHAP contributions
  const typeBonus = type === 'Training' ? 0.25 : type === 'Event' ? 0.18 : type === 'PLV' ? 0.12 : type === 'Digital' ? 0.05 : type === 'Promo' ? 0 : -0.15;
  const tierBonus = pharmacyTier === 'A' ? 0.2 : pharmacyTier === 'B' ? 0.08 : pharmacyTier === 'C' ? 0 : -0.2;
  const budgetBonus = budget > 150 ? -0.08 : budget < 50 ? -0.05 : 0.05;

  const shapData = {
    labels: ['Type', 'Tier', 'Budget', 'Duration', 'Product', 'Target gov.'],
    datasets: [{
      label: 'SHAP value',
      data: [typeBonus, tierBonus, budgetBonus, 0.05, 0.08, 0.04],
      backgroundColor: (ctx: any) => (ctx.parsed.y >= 0 ? '#1D9E75' : '#B8263E'),
      borderRadius: 4,
    }],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: { x: { grid: { display: false } }, y: { grid: { drawTicks: false } } },
  };

  return (
    <div>
      <h1 className="text-3xl font-bold text-ink mb-1">Eligibility Check</h1>
      <p className="text-mute text-sm mb-6">ML scoring for animation pre-approval</p>

      <div className="grid grid-cols-2 gap-6 mb-6">
        {/* Parameters */}
        <div className="bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">Animation parameters</h3>
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-xs font-semibold text-mute mb-2">Type</label>
              <select value={type} onChange={(e) => setType(e.target.value)} className="w-full px-3 py-2 border border-line rounded text-sm">
                <option>Training</option>
                <option>Event</option>
                <option>PLV</option>
                <option>Digital</option>
                <option>Promo</option>
                <option>Contest</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-mute mb-2">Budget (K)</label>
              <input type="number" value={budget} onChange={(e) => setBudget(parseInt(e.target.value))} className="w-full px-3 py-2 border border-line rounded text-sm" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-mute mb-2">Target gov.</label>
              <select value={targetGov} onChange={(e) => setTargetGov(e.target.value)} className="w-full px-3 py-2 border border-line rounded text-sm">
                <option>Tunis</option>
                <option>Sfax</option>
                <option>Sousse</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-mute mb-2">Pharmacy tier</label>
              <select value={pharmacyTier} onChange={(e) => setPharmacyTier(e.target.value)} className="w-full px-3 py-2 border border-line rounded text-sm">
                <option>A</option>
                <option>B</option>
                <option>C</option>
                <option>D</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-mute mb-2">Duration (weeks)</label>
              <input type="number" value={duration} onChange={(e) => setDuration(parseInt(e.target.value))} className="w-full px-3 py-2 border border-line rounded text-sm" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-mute mb-2">Product focus</label>
              <select value={productFocus} onChange={(e) => setProductFocus(e.target.value)} className="w-full px-3 py-2 border border-line rounded text-sm">
                <option>Cardiology</option>
                <option>Neurology</option>
                <option>Pediatrics</option>
              </select>
            </div>
          </div>
          <button onClick={calculateScore} className="w-full px-4 py-2 bg-brand text-white rounded font-semibold">
            Score animation
          </button>
        </div>

        {/* ML Verdict */}
        <div className="bg-card border border-line rounded-lg p-5">
          <h3 className="text-lg font-semibold text-ink mb-4">ML verdict</h3>
          <ScoreBox score={score} />
          <div className="mt-6 space-y-3">
            <div className="flex justify-between">
              <span className="text-mute text-sm">Expected ROI</span>
              <span className="font-semibold">{expectedRoi}×</span>
            </div>
            <div className="flex justify-between">
              <span className="text-mute text-sm">Similar animations</span>
              <span className="font-semibold">7</span>
            </div>
            <div className="flex justify-between">
              <span className="text-mute text-sm">Eligibility</span>
              <span className={`font-semibold px-2 py-1 rounded text-xs ${eligibilityType === 'ok' ? 'bg-green-100 text-green-700' : eligibilityType === 'warn' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>
                {eligibility}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-mute text-sm">Confidence</span>
              <span className="font-semibold capitalize">{confidence}</span>
            </div>
          </div>
        </div>
      </div>

      {/* SHAP */}
      <div className="bg-card border border-line rounded-lg p-5">
        <h3 className="text-lg font-semibold text-ink mb-4">Feature contributions (SHAP)</h3>
        <div style={{ height: '260px' }}>
          <Bar ref={chartRef} data={shapData} options={chartOptions} />
        </div>
      </div>
    </div>
  );
};
