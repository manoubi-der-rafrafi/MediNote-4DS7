import React, { useState } from 'react';
import { useManagerDashboard, useManagerDelegates } from '@/services/queries';
import { QueryWrapper, SkeletonCard, ErrorMessage, LoadingSpinner } from '@/components/LoadingStates';

/**
 * EXAMPLE: Manager Dashboard Integration with Real Backend
 * 
 * This shows the complete pattern for connecting a component to the backend API
 * Copy this pattern to other pages (Direction, Marketing)
 * 
 * Backend: GET /api/commercial
 * Expected response: { data: { delegates: [...], churn_risk: [...], zone_performance: [...] } }
 */

interface Delegate {
  id: number;
  name: string;
  initials: string;
  region: string;
  objective: number;
  score: number;
  status: 'success' | 'warning' | 'danger';
  churn_risk: boolean;
  tier: string;
}

interface ChurnRisk {
  delegate_id: number;
  delegate_name: string;
  risk_score: number;
  reason: string;
}

interface Alert {
  id: number;
  type: string;
  time: string;
  title: string;
  description: string;
  actions: string[];
  severity: 'CRITICAL' | 'URGENT' | 'WATCH';
}

/**
 * Delegate Ranking Card Component
 */
const DelegateCard: React.FC<{ delegate: Delegate; rank: number }> = ({
  delegate,
  rank,
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-100 text-green-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      case 'danger':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 mb-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">
            {rank}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              {delegate.name}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {delegate.region}
            </p>
          </div>
        </div>
        <div className="text-right">
          <div className={`inline-block px-2 py-1 rounded text-sm font-semibold ${getStatusColor(delegate.status)}`}>
            {(delegate.score * 100).toFixed(0)}%
          </div>
          {delegate.churn_risk && (
            <div className="text-xs text-red-600 mt-1">⚠️ Churn Risk</div>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * Alerts Section Component
 */
const AlertsList: React.FC<{ alerts: Alert[] }> = ({ alerts }) => {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'border-l-4 border-red-500 bg-red-50 dark:bg-red-900/20';
      case 'URGENT':
        return 'border-l-4 border-orange-500 bg-orange-50 dark:bg-orange-900/20';
      case 'WATCH':
        return 'border-l-4 border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20';
      default:
        return 'border-l-4 border-gray-500';
    }
  };

  return (
    <div className="space-y-3">
      {alerts.map(alert => (
        <div key={alert.id} className={`p-4 rounded ${getSeverityColor(alert.severity)}`}>
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-1">
                {alert.title}
              </h4>
              <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                {alert.description}
              </p>
              <div className="flex gap-2">
                {alert.actions.map(action => (
                  <button
                    key={action}
                    className="text-xs px-2 py-1 bg-white dark:bg-gray-800 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition"
                  >
                    {action}
                  </button>
                ))}
              </div>
            </div>
            <span className="text-xs text-gray-500 ml-2">{alert.time}</span>
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * Main Manager Dashboard Component
 * 
 * Integration pattern:
 * 1. Call useManagerDashboard() hook
 * 2. Handle loading, error states with QueryWrapper
 * 3. Map backend data to UI components
 * 4. Provide retry callback on error
 */
export const ManagerDashboardIntegrated: React.FC = () => {
  // 1. Fetch data from backend
  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
  } = useManagerDashboard();

  // 2. Optional: Manual filtering
  const [filterTier, setFilterTier] = useState<string | null>(null);

  // Transform backend data to component format
  const delegates = (data?.data?.delegates || []) as Delegate[];
  const alerts = (data?.data?.alerts || []) as Alert[];
  const churnRisks = (data?.data?.churn_risk || []) as ChurnRisk[];

  // Filter if needed
  const filteredDelegates = filterTier
    ? delegates.filter(d => d.tier === filterTier)
    : delegates;

  return (
    <div className="p-6 bg-gray-50 dark:bg-gray-900 min-h-screen">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Manager Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Real-time team performance and alerts
          </p>
        </div>

        {/* Refresh Button */}
        <div className="mb-4">
          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {isLoading ? <LoadingSpinner size="sm" /> : '🔄 Refresh'}
          </button>
        </div>

        {/* Main Content with Loading/Error Handling */}
        <QueryWrapper
          isLoading={isLoading}
          isError={isError}
          error={error}
          data={data}
          loadingComponent={<SkeletonCard count={5} />}
          onRetry={() => refetch()}
        >
          {/* Two-column layout */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Delegates & KPIs */}
            <div className="lg:col-span-2 space-y-6">
              {/* KPIs Summary */}
              <div className="grid grid-cols-2 gap-4 bg-white dark:bg-gray-800 rounded-lg p-4">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Total Delegates
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {delegates.length}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Churn Risk
                  </p>
                  <p className="text-2xl font-bold text-red-600">
                    {churnRisks.length}
                  </p>
                </div>
              </div>

              {/* Filters */}
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                  Delegate Rankings
                </h2>
                <div className="flex gap-2 mb-4">
                  <button
                    onClick={() => setFilterTier(null)}
                    className={`px-3 py-1 rounded text-sm ${
                      filterTier === null
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white'
                    }`}
                  >
                    All
                  </button>
                  {['A', 'B', 'C'].map(tier => (
                    <button
                      key={tier}
                      onClick={() => setFilterTier(tier)}
                      className={`px-3 py-1 rounded text-sm ${
                        filterTier === tier
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white'
                      }`}
                    >
                      Tier {tier}
                    </button>
                  ))}
                </div>
              </div>

              {/* Delegate List */}
              <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
                {filteredDelegates.length > 0 ? (
                  filteredDelegates.map((delegate, index) => (
                    <DelegateCard
                      key={delegate.id}
                      delegate={delegate}
                      rank={index + 1}
                    />
                  ))
                ) : (
                  <p className="text-center text-gray-500 py-8">
                    No delegates found
                  </p>
                )}
              </div>
            </div>

            {/* Right: Alerts */}
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 h-fit">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Alerts & Actions
              </h2>
              {alerts.length > 0 ? (
                <AlertsList alerts={alerts.slice(0, 5)} />
              ) : (
                <p className="text-center text-gray-500 py-8">
                  No alerts
                </p>
              )}
            </div>
          </div>
        </QueryWrapper>
      </div>
    </div>
  );
};

export default ManagerDashboardIntegrated;
