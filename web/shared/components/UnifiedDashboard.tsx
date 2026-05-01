import React, { useEffect, useState } from 'react';
import { User } from '../lib/auth';
import { BarChart3, TrendingUp, Users, Target, AlertCircle, DollarSign } from 'lucide-react';

interface DashboardProps {
  user: User | null;
}

interface DashboardData {
  success: boolean;
  role: string;
  data: Record<string, any>;
  timestamp: string;
}

export const UnifiedDashboard: React.FC<DashboardProps> = ({ user }) => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;

    const fetchDashboard = async () => {
      try {
        setLoading(true);
        setError(null);

        const endpoint = `/api/dashboard/${user.role}`;
        const response = await fetch(endpoint, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'X-User-Role': user.role,
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch dashboard: ${response.statusText}`);
        }

        const data: DashboardData = await response.json();
        setDashboardData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard');
        console.error('Dashboard fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, [user]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Chargement du tableau de bord...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-lg text-red-400">
        <p className="font-semibold mb-2">Erreur</p>
        <p className="text-sm">{error}</p>
      </div>
    );
  }

  if (!dashboardData) {
    return <div className="text-gray-400">Aucune donnée disponible</div>;
  }

  // Render role-specific content
  switch (user?.role) {
    case 'manager':
      return <ManagerDashboard data={dashboardData.data} />;
    case 'marketing':
      return <MarketingDashboard data={dashboardData.data} />;
    case 'direction':
      return <DirectionDashboard data={dashboardData.data} />;
    default:
      return <div className="text-gray-400">Rôle non reconnu</div>;
  }
};

// Manager Dashboard Component
const ManagerDashboard: React.FC<{ data: Record<string, any> }> = ({ data }) => {
  const teamOverview = data.team_overview || {};
  const territories = data.territories || {};
  const topPerformers = data.top_performers || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Tableau de Bord Manager</h1>
        <p className="text-gray-400">Gestion des délégués et performances territoriales</p>
      </div>

      {/* KPI Cards */}
      <div className="grid md:grid-cols-4 gap-4">
        <KPICard
          icon={<Users />}
          title="Délégués Actifs"
          value={teamOverview.total_delegates}
          unit="équipe"
          color="blue"
        />
        <KPICard
          icon={<Target />}
          title="Territoires Couverts"
          value={territories.covered}
          unit={`/${territories.total}`}
          color="green"
        />
        <KPICard
          icon={<TrendingUp />}
          title="Performance Moyenne"
          value={teamOverview.average_performance}
          unit="%"
          color="purple"
        />
        <KPICard
          icon={<AlertCircle />}
          title="Alertes en Attente"
          value={teamOverview.alerts}
          unit="urgentes"
          color="red"
        />
      </div>

      {/* Top Performers */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Users size={24} />
          Top Performers
        </h2>
        <div className="space-y-3">
          {topPerformers.map((performer: any, idx: number) => (
            <div key={idx} className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-colors">
              <div>
                <p className="font-semibold text-white">{performer.name}</p>
                <p className="text-sm text-gray-400">{performer.territory}</p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-green-400">{performer.score}</div>
                <div className="text-xs text-gray-500">{performer.calls} appels</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Marketing Dashboard Component
const MarketingDashboard: React.FC<{ data: Record<string, any> }> = ({ data }) => {
  const campaigns = data.campaigns || {};
  const segments = data.segments || [];
  const sentiment = data.sentiment_analysis || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Tableau de Bord Marketing</h1>
        <p className="text-gray-400">Campagnes, segmentation et analyse sentimentale</p>
      </div>

      {/* Campaign Metrics */}
      <div className="grid md:grid-cols-4 gap-4">
        <KPICard
          icon={<Target />}
          title="Campagnes Actives"
          value={campaigns.active}
          unit="en cours"
          color="blue"
        />
        <KPICard
          icon={<Users />}
          title="Portée Totale"
          value={campaigns.total_reach}
          unit="médecins"
          color="green"
        />
        <KPICard
          icon={<DollarSign />}
          title="Budget Alloué"
          value={campaigns.budget_allocated}
          unit=""
          color="yellow"
        />
        <KPICard
          icon={<TrendingUp />}
          title="ROI Moyen"
          value={campaigns.avg_roi}
          unit=""
          color="purple"
        />
      </div>

      {/* Segments */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">Segments de Clientèle</h2>
        <div className="space-y-3">
          {segments.map((segment: any, idx: number) => (
            <div key={idx} className="p-4 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-white">{segment.name}</h3>
                <span className="text-green-400 font-bold">{segment.growth}</span>
              </div>
              <div className="flex gap-4 text-sm text-gray-400">
                <span>{segment.doctors} médecins</span>
                <span>Engagement: {segment.engagement}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Sentiment Analysis */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">Analyse Sentimentale</h2>
        <div className="grid md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-3xl font-bold text-green-400 mb-2">{sentiment.positive_ratio}</div>
            <p className="text-gray-400">Positif</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-yellow-400 mb-2">{sentiment.neutral_ratio}</div>
            <p className="text-gray-400">Neutre</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-red-400 mb-2">{sentiment.negative_ratio}</div>
            <p className="text-gray-400">Négatif</p>
          </div>
        </div>
        <p className="text-sm text-gray-500 text-center mt-4">{sentiment.comments_analyzed} commentaires analysés</p>
      </div>
    </div>
  );
};

// Direction Dashboard Component
const DirectionDashboard: React.FC<{ data: Record<string, any> }> = ({ data }) => {
  const brief = data.executive_brief || {};
  const kpis = data.kpis || {};
  const forecasts = data.forecasts || {};
  const regions = data.regional_breakdown || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Tableau de Bord Exécutif</h1>
        <p className="text-gray-400">Vue stratégique et indicateurs clés de performance</p>
      </div>

      {/* Executive Brief */}
      <div className="grid md:grid-cols-4 gap-4">
        <KPICard
          icon={<DollarSign />}
          title="Chiffre d'Affaires YTD"
          value={brief.revenue_ytd}
          unit=""
          color="green"
        />
        <KPICard
          icon={<TrendingUp />}
          title="Taux de Croissance"
          value={brief.growth_rate}
          unit=""
          color="blue"
        />
        <KPICard
          icon={<Target />}
          title="Atteinte des Objectifs"
          value={brief.target_achievement}
          unit="%"
          color="purple"
        />
        <KPICard
          icon={<AlertCircle />}
          title="Alertes Critiques"
          value={brief.critical_alerts}
          unit="en cours"
          color="red"
        />
      </div>

      {/* KPIs Grid */}
      <div className="grid md:grid-cols-3 gap-4">
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Part de Marché</p>
          <p className="text-3xl font-bold text-green-400">{kpis.market_share}</p>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Couverture Médecins</p>
          <p className="text-3xl font-bold text-blue-400">{kpis.doctor_coverage}</p>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Tendance Prescriptions</p>
          <p className="text-3xl font-bold text-purple-400">{kpis.prescription_trend}</p>
        </div>
      </div>

      {/* Forecasts */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <BarChart3 size={24} />
          Projections
        </h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg">
            <span className="text-gray-300">Projection Q2</span>
            <span className="text-2xl font-bold text-green-400">{forecasts.q2_projection}</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg">
            <span className="text-gray-300">Scénario Optimiste</span>
            <span className="text-2xl font-bold text-green-400">{forecasts.scenario_optimistic}</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg">
            <span className="text-gray-300">Scénario Pessimiste</span>
            <span className="text-2xl font-bold text-red-400">{forecasts.scenario_pessimistic}</span>
          </div>
        </div>
      </div>

      {/* Regional Breakdown */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">Répartition Régionale</h2>
        <div className="space-y-2">
          {regions.map((region: any, idx: number) => (
            <div key={idx} className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-colors">
              <div>
                <p className="font-semibold text-white">{region.region}</p>
                <p className="text-sm text-gray-400">Responsable: {region.lead}</p>
              </div>
              <p className="text-xl font-bold text-purple-400">{region.revenue}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// KPI Card Component
interface KPICardProps {
  icon: React.ReactNode;
  title: string;
  value: string | number;
  unit: string;
  color: 'blue' | 'green' | 'purple' | 'red' | 'yellow';
}

const KPICard: React.FC<KPICardProps> = ({ icon, title, value, unit, color }) => {
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-900/20 border-blue-500/30',
    green: 'bg-green-900/20 border-green-500/30',
    purple: 'bg-purple-900/20 border-purple-500/30',
    red: 'bg-red-900/20 border-red-500/30',
    yellow: 'bg-yellow-900/20 border-yellow-500/30',
  };

  const textColorClasses: Record<string, string> = {
    blue: 'text-blue-400',
    green: 'text-green-400',
    purple: 'text-purple-400',
    red: 'text-red-400',
    yellow: 'text-yellow-400',
  };

  return (
    <div className={`${colorClasses[color]} border rounded-lg p-4`}>
      <div className="flex items-start justify-between mb-3">
        <div className={`${textColorClasses[color]} opacity-70`}>{icon}</div>
      </div>
      <p className="text-gray-400 text-sm mb-1">{title}</p>
      <div className="flex items-baseline gap-2">
        <span className={`text-2xl font-bold ${textColorClasses[color]}`}>{value}</span>
        {unit && <span className="text-xs text-gray-500">{unit}</span>}
      </div>
    </div>
  );
};
