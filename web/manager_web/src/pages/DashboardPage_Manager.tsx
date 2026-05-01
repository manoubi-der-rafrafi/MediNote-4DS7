import React from 'react';
import { useManagerDashboard } from '../services/queries';
import { QueryWrapper, SkeletonCard } from '../components/LoadingStates';

// Design tokens - copied inline for this component
const theme = {
  colors: {
    bg: '#080910',
    s1: '#0F1113',
    s2: '#1A1D21',
    blue: '#5B8DF6',
    green: '#3DD68C',
    red: '#F06565',
    amber: '#F59E0B',
    purple: '#8B5CF6',
    white: '#FFFFFF',
    gray: '#9CA3AF',
    b1: '#2A2D33',
    b2: '#3F4249',
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
  },
  radius: {
    r: '8px',
    r2: '12px',
    r3: '16px',
  },
};

export const ManagerDashboard: React.FC = () => {
  // Fetch real data from backend
  const { data, isLoading, isError, error, refetch } = useManagerDashboard();

  // Transform backend data to UI format
  const agentData = data?.data;

  const getKPIs = () => {
    const scorecards = agentData?.delegate_scorecards || [];
    const avgScore = scorecards.length
      ? (scorecards.reduce((s: number, d: any) => s + (d.score_normalized || 0), 0) / scorecards.length).toFixed(2)
      : '—';
    const avgAchievement = scorecards.length
      ? Math.round(scorecards.reduce((s: number, d: any) => s + (d.ca_achievement_pct || 0), 0) / scorecards.length)
      : '—';
    const atRisk = agentData?.predictions?.delegates_at_risk_missing_target?.count ?? '—';
    const total = agentData?.total_delegates ?? scorecards.length;
    return [
      { value: total ? `${total}` : '—', label: 'Délégués analysés', delta: 'données notebook enrichi' },
      { value: `${avgScore}`, label: 'Score composite moyen', delta: 'composite_score_enriched' },
      { value: avgAchievement !== '—' ? `${avgAchievement}%` : '—', label: 'Réalisation obj. moyen', delta: 'avg_achievement' },
      { value: `${atRisk}`, label: 'Délégués à risque', delta: '⚠ Action requise' },
    ];
  };

  const getDelegates = () => {
    if (!agentData?.delegate_scorecards) return [];
    return agentData?.delegate_scorecards?.slice(0, 4).map((d: any) => ({
      rank: d.rank || 0,
      initials: String(d.id_delegate || 'XX').substring(0, 2).toUpperCase(),
      name: `Délégué ${d.id_delegate}`,
      region: d.zone || d.gouvernorat || d.region || 'N/A',
      objective: Math.round(d.ca_achievement_pct || 0),
      score: (d.score_normalized || 0) / 100,
      status: (d.score_normalized || 0) > 75 ? 'success' : (d.score_normalized || 0) > 55 ? 'warning' : 'danger',
    }));
  };

  const getAlerts = () => {
    const alerts: any[] = [];
    agentData?.predictions?.delegates_at_risk_missing_target?.delegates?.slice(0, 2).forEach((d: any, i: number) => {
      alerts.push({
        id: i + 1,
        type: 'compliance',
        time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
        title: `Risque objectif · Délégué ${d.id_delegate}`,
        description: `Score: ${Math.round(d.score_normalized || 0)}% · Réalisation: ${Math.round(d.ca_achievement_pct || 0)}%`,
        actions: ['Voir dossier', 'Contacter'],
      });
    });
    agentData?.predictions?.delegates_with_churn_risk?.delegates?.slice(0, 1).forEach((d: any) => {
      alerts.push({
        id: 10,
        type: 'coaching',
        time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
        title: `Plan coaching · Délégué ${d.id_delegate}`,
        description: `Risk total: ${(d.predictions?.overall_risk_score_pct || 0).toFixed(0)}% · Prospects: ${d.total_prospects || 0}`,
        actions: ['Valider plan', 'Modifier'],
      });
    });
    return alerts;
  };

  const getRiskZones = () => {
    if (!agentData?.zone_performance?.bottom_zones) return [];
    return agentData?.zone_performance?.bottom_zones?.map((z: any) => ({
      name: z.zone || 'Zone',
      doctors: z.num_delegates || 0,
      days: Math.round(z.avg_achievement || 0),
    }));
  };

  const getSuggestions = () => {
    const suggestions: any[] = [];
    const top = agentData?.clustering_details?.details?.high_performers?.[0];
    if (top) {
      suggestions.push({
        action: `Top performer: Délégué ${top.id_delegate}`,
        impact: `Score composite: ${Math.round(top.score_normalized || 0)}%`,
      });
    }
    const coverage = agentData?.prospect_coverage;
    if (coverage?.delegates_below_10_prospects > 0) {
      suggestions.push({
        action: `${coverage.delegates_below_10_prospects} délégués < 10 prospects`,
        impact: `Couverture moyenne: ${coverage.avg_prospects_per_delegate?.toFixed(1)} prospects`,
      });
    }
    return suggestions;
  };

  const delegates = getDelegates();
  const alerts = getAlerts();
  const riskZones = getRiskZones();
  const suggestions = getSuggestions();

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return theme.colors.green;
      case 'warning': return theme.colors.amber;
      case 'danger': return theme.colors.red;
      default: return theme.colors.gray;
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'success': return '✓ OK';
      case 'warning': return '⚠ Coaching';
      case 'danger': return '🚨 Tier H';
      default: return 'N/A';
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'compliance': return '🚨';
      case 'coaching': return '🎯';
      case 'territory': return '◎';
      default: return '●';
    }
  };

  return (
    <QueryWrapper
      isLoading={isLoading}
      isError={isError}
      error={error}
      data={data}
      loadingComponent={<SkeletonCard count={4} />}
      onRetry={() => refetch()}
    >
      <div style={{ padding: theme.spacing.xl, background: theme.colors.bg, minHeight: '100vh' }}>
      {/* Header Section */}
      <div style={{ marginBottom: theme.spacing.xl }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: theme.spacing.lg }}>
          <div>
            <h1 style={{ fontSize: '28px', fontWeight: 800, color: theme.colors.white, margin: 0 }}>
              PharmaCRM
            </h1>
            <p style={{ fontSize: '14px', color: theme.colors.gray, margin: '4px 0 0 0' }}>
              Manager · Région Sud-Ouest
            </p>
          </div>
          <div style={{ display: 'flex', gap: theme.spacing.sm }}>
            <button style={{
              padding: `${theme.spacing.sm} ${theme.spacing.md}`,
              background: theme.colors.s1,
              border: `1px solid ${theme.colors.b1}`,
              color: theme.colors.white,
              borderRadius: theme.radius.r2,
              cursor: 'pointer',
              fontSize: '12px',
            }}>
              ⚙ Config
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: theme.spacing.lg, marginBottom: theme.spacing.xl }}>
        {/* Left Column - KPIs and Delegates */}
        <div>
          {/* KPI Row */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: theme.spacing.md, marginBottom: theme.spacing.lg }}>
            {getKPIs().map((kpi, i) => (
              <div key={i} style={{
                background: theme.colors.s1,
                border: `1px solid ${theme.colors.b1}`,
                borderRadius: theme.radius.r2,
                padding: theme.spacing.lg,
              }}>
                <div style={{ fontSize: '28px', fontWeight: 800, color: theme.colors.white, marginBottom: '4px' }}>
                  {kpi.value}
                </div>
                <div style={{ fontSize: '12px', color: theme.colors.gray, marginBottom: '8px' }}>
                  {kpi.label}
                </div>
                <div style={{ fontSize: '11px', color: theme.colors.blue }}>
                  {kpi.delta}
                </div>
              </div>
            ))}
          </div>

          {/* Delegate Table */}
          <div style={{
            background: theme.colors.s1,
            border: `1px solid ${theme.colors.b1}`,
            borderRadius: theme.radius.r2,
            overflow: 'hidden',
          }}>
            <div style={{
              padding: theme.spacing.lg,
              background: theme.colors.s2,
              borderBottom: `1px solid ${theme.colors.b1}`,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}>
              <h3 style={{ margin: 0, fontSize: '14px', fontWeight: 600, color: theme.colors.white }}>
                Classement délégués
              </h3>
              <a href="#" style={{ fontSize: '12px', color: theme.colors.blue, textDecoration: 'none' }}>
                Voir tout →
              </a>
            </div>

            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${theme.colors.b1}` }}>
                  <th style={{ padding: theme.spacing.md, textAlign: 'left', fontSize: '12px', color: theme.colors.gray, fontWeight: 600 }}>#</th>
                  <th style={{ padding: theme.spacing.md, textAlign: 'left', fontSize: '12px', color: theme.colors.gray, fontWeight: 600 }}>Délégué</th>
                  <th style={{ padding: theme.spacing.md, textAlign: 'left', fontSize: '12px', color: theme.colors.gray, fontWeight: 600 }}>Objectif</th>
                  <th style={{ padding: theme.spacing.md, textAlign: 'left', fontSize: '12px', color: theme.colors.gray, fontWeight: 600 }}>DS7</th>
                  <th style={{ padding: theme.spacing.md, textAlign: 'left', fontSize: '12px', color: theme.colors.gray, fontWeight: 600 }}>Statut</th>
                </tr>
              </thead>
              <tbody>
                {delegates.map((d: any, i: number) => (
                  <tr key={d.rank} style={{
                    borderBottom: i < delegates.length - 1 ? `1px solid ${theme.colors.b1}` : 'none',
                    background: i % 2 === 0 ? 'transparent' : theme.colors.s2,
                  }}>
                    <td style={{ padding: theme.spacing.md, fontSize: '12px', color: theme.colors.gray }}>{d.rank}</td>
                    <td style={{ padding: theme.spacing.md }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm }}>
                        <div style={{
                          width: '28px',
                          height: '28px',
                          borderRadius: '50%',
                          background: theme.colors.purple,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '11px',
                          fontWeight: 700,
                          color: theme.colors.white,
                        }}>
                          {d.initials}
                        </div>
                        <div>
                          <div style={{ fontSize: '12px', color: theme.colors.white, fontWeight: 500 }}>{d.name}</div>
                          <div style={{ fontSize: '11px', color: theme.colors.gray }}>{d.region}</div>
                        </div>
                      </div>
                    </td>
                    <td style={{ padding: theme.spacing.md }}>
                      <div style={{ fontSize: '12px', color: theme.colors.white, fontWeight: 600 }}>{d.objective}%</div>
                    </td>
                    <td style={{ padding: theme.spacing.md, fontSize: '12px', color: theme.colors.white }}>{d.score.toFixed(2)}</td>
                    <td style={{ padding: theme.spacing.md }}>
                      <div style={{
                        display: 'inline-block',
                        padding: '4px 8px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        color: getStatusColor(d.status),
                        background: `${getStatusColor(d.status)}20`,
                        border: `1px solid ${getStatusColor(d.status)}40`,
                      }}>
                        {getStatusLabel(d.status)}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column - Alerts and Territory */}
        <div>
          {/* Alerts Section */}
          <div style={{
            background: theme.colors.s1,
            border: `1px solid ${theme.colors.b1}`,
            borderRadius: theme.radius.r2,
            overflow: 'hidden',
            marginBottom: theme.spacing.lg,
          }}>
            <div style={{
              padding: theme.spacing.lg,
              background: theme.colors.s2,
              borderBottom: `1px solid ${theme.colors.b1}`,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}>
              <h3 style={{ margin: 0, fontSize: '14px', fontWeight: 600, color: theme.colors.white }}>
                Alertes agents
              </h3>
              <a href="#" style={{ fontSize: '12px', color: theme.colors.blue, textDecoration: 'none' }}>
                Tout marquer lu
              </a>
            </div>

            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {alerts.map((alert, i) => (
                <div key={alert.id} style={{
                  padding: theme.spacing.lg,
                  borderBottom: i < alerts.length - 1 ? `1px solid ${theme.colors.b1}` : 'none',
                }}>
                  <div style={{ display: 'flex', gap: theme.spacing.md, marginBottom: theme.spacing.sm }}>
                    <div style={{ fontSize: '18px' }}>{getAlertIcon(alert.type)}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '12px', fontWeight: 600, color: theme.colors.white }}>
                        {alert.title}
                      </div>
                      <div style={{ fontSize: '11px', color: theme.colors.gray, marginTop: '4px' }}>
                        {alert.description}
                      </div>
                      <div style={{ display: 'flex', gap: theme.spacing.sm, marginTop: theme.spacing.sm }}>
                        {alert.actions.map((action: string, j: number) => (
                          <button key={j} style={{
                            padding: '4px 10px',
                            fontSize: '11px',
                            background: theme.colors.blue,
                            color: theme.colors.white,
                            border: 'none',
                            borderRadius: theme.radius.r,
                            cursor: 'pointer',
                          }}>
                            {action}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div style={{ fontSize: '11px', color: theme.colors.gray, whiteSpace: 'nowrap' }}>
                      {alert.time}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Territory Card */}
          <div style={{
            background: theme.colors.s1,
            border: `1px solid ${theme.colors.b1}`,
            borderRadius: theme.radius.r2,
            overflow: 'hidden',
          }}>
            <div style={{
              padding: theme.spacing.lg,
              background: theme.colors.s2,
              borderBottom: `1px solid ${theme.colors.b1}`,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}>
              <h3 style={{ margin: 0, fontSize: '14px', fontWeight: 600, color: theme.colors.white }}>
                Territoire · Couverture région Sud-Ouest
              </h3>
              <a href="#" style={{ fontSize: '12px', color: theme.colors.blue, textDecoration: 'none' }}>
                Vue carte complète →
              </a>
            </div>

            <div style={{ padding: theme.spacing.lg }}>
              <div style={{ marginBottom: theme.spacing.lg }}>
                <h4 style={{ margin: 0, fontSize: '12px', fontWeight: 600, color: theme.colors.red, marginBottom: theme.spacing.md }}>
                  ⚠ Zones à risque détectées
                </h4>
                {riskZones.map((zone: any, i: number) => (
                  <div key={i} style={{
                    padding: theme.spacing.sm,
                    fontSize: '12px',
                    color: theme.colors.white,
                    borderBottom: i < riskZones.length - 1 ? `1px solid ${theme.colors.b1}` : 'none',
                  }}>
                    <div style={{ fontWeight: 600 }}>{zone.name}</div>
                    <div style={{ fontSize: '11px', color: theme.colors.gray }}>
                      {zone.doctors} méd. · {zone.days}j
                    </div>
                  </div>
                ))}
              </div>

              <div>
                <h4 style={{ margin: 0, fontSize: '12px', fontWeight: 600, color: theme.colors.green, marginBottom: theme.spacing.md }}>
                  ✓ Suggestions Agent Territoire
                </h4>
                {suggestions.map((sugg, i) => (
                  <div key={i} style={{
                    padding: theme.spacing.sm,
                    fontSize: '12px',
                    color: theme.colors.white,
                  }}>
                    <div>→ {sugg.action}</div>
                    <div style={{ fontSize: '11px', color: theme.colors.gray }}>
                      {sugg.impact}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    </QueryWrapper>
  );
};

export default ManagerDashboard;
