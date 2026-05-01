// Page: Forecast — App: Manager — API: /api/v1/manager/forecast
import React, { useState } from 'react';
import { PageHeader } from '../components/ui/PageHeader';
import { ScenarioCard } from '../components/ui/ScenarioCard';
import { ForecastChart } from '../components/ui/ForecastChart';
import { Badge } from '../components/ui/Badge';

type Metric = 'CA' | 'VISITES' | 'RX' | 'PARTS_MARCHE';
type Horizon = '3m' | '6m' | '12m';
type Scope = 'TEAM' | 'REGION';

const mockForecastData = [
  { month: 'Apr', pessimiste: 2100000, realiste: 2400000, optimiste: 2800000 },
  { month: 'May', pessimiste: 2050000, realiste: 2500000, optimiste: 3000000 },
  { month: 'Jun', pessimiste: 2000000, realiste: 2580000, optimiste: 3200000 },
  { month: 'Jul', pessimiste: 1950000, realiste: 2700000, optimiste: 3400000 },
  { month: 'Aug', pessimiste: 1900000, realiste: 2800000, optimiste: 3600000 },
  { month: 'Sep', pessimiste: 1850000, realiste: 2900000, optimiste: 3800000 },
  { month: 'Oct', pessimiste: 1800000, realiste: 3000000, optimiste: 4000000 },
  { month: 'Nov', pessimiste: 1750000, realiste: 3100000, optimiste: 4200000 },
  { month: 'Dec', pessimiste: 1700000, realiste: 3200000, optimiste: 4400000 },
];

export const ForecastPage: React.FC = () => {
  const [metric, setMetric] = useState<Metric>('CA');
  const [horizon, setHorizon] = useState<Horizon>('12m');
  const [scope, setScope] = useState<Scope>('TEAM');

  const assumptions = {
    pessimiste: [
      'Réduction 20% des visites',
      'Absence nouvelles animations',
      'Effets saisonniers négatifs',
      'Turnover délégué',
    ],
    realiste: [
      'Tendance actuelle maintenue',
      'Growth organique 10%',
      '2 nouvelles animations',
      'Stabilité équipe',
    ],
    optimiste: [
      'Accélération visites +25%',
      'Succès animations +40%',
      'Recrutement nouveau délégué',
      'Expansion géographique',
    ],
  };

  return (
    <div>
      <PageHeader
        title="Prévisions"
        subtitle="Généré par Agent_Forecast"
      />

      {/* Controls */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div>
          <label className="block text-xs font-semibold text-gray-300 mb-2">Métrique</label>
          <select
            value={metric}
            onChange={e => setMetric(e.target.value as Metric)}
            className="w-full px-3 py-2 bg-s1 border border-bd rounded text-sm text-white focus:outline-none focus:border-manager"
          >
            <option value="CA">CA</option>
            <option value="VISITES">Visites</option>
            <option value="RX">Rx</option>
            <option value="PARTS_MARCHE">Parts de marché</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-300 mb-2">Horizon</label>
          <select
            value={horizon}
            onChange={e => setHorizon(e.target.value as Horizon)}
            className="w-full px-3 py-2 bg-s1 border border-bd rounded text-sm text-white focus:outline-none focus:border-manager"
          >
            <option value="3m">3 mois</option>
            <option value="6m">6 mois</option>
            <option value="12m">12 mois</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-300 mb-2">Périmètre</label>
          <select
            value={scope}
            onChange={e => setScope(e.target.value as Scope)}
            className="w-full px-3 py-2 bg-s1 border border-bd rounded text-sm text-white focus:outline-none focus:border-manager"
          >
            <option value="TEAM">Mon équipe</option>
            <option value="REGION">Toute la région</option>
          </select>
        </div>

        <div className="flex items-end">
          <button className="w-full px-4 py-2 bg-manager text-white rounded-lg font-semibold hover:opacity-90 transition-opacity">
            Générer
          </button>
        </div>
      </div>

      {/* Scenario Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <ScenarioCard
          scenario="pessimiste"
          value="1.7M"
          unit="MAD"
          delta={-28}
          color="red"
          assumptions={assumptions.pessimiste}
        />
        <ScenarioCard
          scenario="realiste"
          value="3.2M"
          unit="MAD"
          delta={15}
          color="blue"
          assumptions={assumptions.realiste}
        />
        <ScenarioCard
          scenario="optimiste"
          value="4.4M"
          unit="MAD"
          delta={42}
          color="green"
          assumptions={assumptions.optimiste}
        />
      </div>

      {/* Forecast Chart */}
      <div className="bg-s1 border border-bd rounded-lg p-6 mb-6">
        <ForecastChart data={mockForecastData} />
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Products */}
        <div className="bg-s1 border border-bd rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Par produit</h3>
          <div className="space-y-3">
            {[
              { product: 'Paracétamol 500mg', current: 450000, forecast: 520000, risk: 'LOW' },
              { product: 'Ibuprofène 200mg', current: 380000, forecast: 420000, risk: 'LOW' },
              { product: 'Amoxicilline 500mg', current: 320000, forecast: 380000, risk: 'MEDIUM' },
            ].map((item, idx) => (
              <div key={idx} className="p-3 bg-s2 rounded border border-bd">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold">{item.product}</span>
                  <Badge
                    variant={item.risk === 'LOW' ? 'success' : item.risk === 'MEDIUM' ? 'warning' : 'danger'}
                  >
                    {item.risk}
                  </Badge>
                </div>
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>Current: {(item.current / 1000).toFixed(0)}K</span>
                  <span>Forecast: {(item.forecast / 1000).toFixed(0)}K</span>
                  <span className="text-green">↑ {(((item.forecast - item.current) / item.current) * 100).toFixed(0)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Risks */}
        <div className="bg-s1 border border-bd rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Risques stratégiques</h3>
          <div className="space-y-2">
            {[
              { risk: 'Turnover délégué Casablanca', severity: 'CRITICAL', agent: 'Agent_HR' },
              { risk: 'Anomalie KPI région Fès', severity: 'URGENT', agent: 'Agent_Anomaly' },
              { risk: 'Stock faible produit phare', severity: 'WATCH', agent: 'Agent_Stock', },
            ].map((item, idx) => (
              <div key={idx} className="p-3 bg-s2 rounded border border-bd flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold">{item.risk}</p>
                  <p className="text-xs text-gray-400">{item.agent}</p>
                </div>
                <Badge
                  variant={
                    item.severity === 'CRITICAL'
                      ? 'danger'
                      : item.severity === 'URGENT'
                        ? 'warning'
                        : 'info'
                  }
                >
                  {item.severity}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
