// ─── Screen 4: Mon score délégué ─────────────────────────────────────────────
// Notebooks: Nb05 (scoring multi-dim — notes/commissions/CAPH/CAGRO/NLP signals)
import React, { useContext } from 'react';
import { View, Text, ScrollView, StyleSheet, SafeAreaView } from 'react-native';
import { colors, spacing, radius } from '../theme';
import { RingChart, ScoreRow, ActionItem, SectionLabel } from '../components';
import { SessionContext } from '../context/SessionContext';
import { useDelegateData } from '../hooks/useDelegateData';

// ─── Data (from delegate_master_table.csv · Nb05) ────────────────────────────
const GLOBAL = { score: 84, label: 'Excellent', rank: '2/10 région · Nb05' };

const COMPONENTS = [
  { label: 'Notes terrain',  score: 8.8, color: colors.green  },
  { label: 'Commissions',    score: 8.2, color: colors.blue   },
  { label: 'CAPH / CAGRO',  score: 7.9, color: colors.purple },
  { label: 'Qualité visite', score: 8.3, color: colors.orange },
  { label: 'Signaux NLP',   score: 7.6, color: colors.teal   },
];

const WEEKLY_BARS = [55, 38, 72, 90, 48, 65, 100]; // % heights

const METRICS = [
  { value: '24',    label: 'Visites semaine', delta: '↑ +4 vs S14', up: true,  color: colors.blue   },
  { value: '0.83',  label: 'Score qualité',  delta: '↑ +0.07',     up: true,  color: colors.green  },
  { value: '87%',   label: 'Objectif mensuel',delta: '↓ −3% cible', up: false, color: colors.purple },
  { value: '0',     label: 'Alertes quota',  delta: '✓ Conforme',   up: true,  color: colors.green  },
];

const ACTIONS = [
  { num: '1', text: 'Reprendre Dr Mbaye — sentiment négatif détecté · Nb12' },
  { num: '2', text: 'Améliorer signaux NLP → +0.3 pts score prédit · Nb05' },
  { num: '3', text: '+3 visites pour atteindre l\'objectif cycle' },
];

// ─── Mini bar chart ────────────────────────────────────────────────────────────
function MiniBarChart({ data }) {
  const BAR_H = 48;
  return (
    <View style={{ flexDirection: 'row', alignItems: 'flex-end', gap: 3, height: BAR_H }}>
      {data.map((pct, i) => (
        <View
          key={i}
          style={{
            flex: 1,
            height: (pct / 100) * BAR_H,
            borderRadius: 3,
            backgroundColor: i % 2 === 0 ? colors.blue : colors.bd2,
            borderTopLeftRadius: 3, borderTopRightRadius: 3,
          }}
        />
      ))}
    </View>
  );
}

// ─── Component ────────────────────────────────────────────────────────────────
export default function ScoreScreen() {
  const session = useContext(SessionContext) || {};
  const delegateId = session.currentDelegate?.id_deleg ?? 541;
  const { scorecard, loading: apiLoading } = useDelegateData(delegateId);

  const globalScore = scorecard?.score_normalized != null
    ? Math.round(scorecard.score_normalized * 100)
    : GLOBAL.score;

  const caAchievement = scorecard?.ca_achievement_pct != null
    ? `${Math.round(scorecard.ca_achievement_pct)}%`
    : '87%';
  const metrics = [...METRICS];
  metrics[2] = { ...metrics[2], value: caAchievement };

  return (
    <SafeAreaView style={s.safe}>
      <View style={s.header}>
        <Text style={s.title}>Ma synthèse · Nb05</Text>
        <Text style={s.sub}>S15 · Scoring multi-dimensionnel</Text>
      </View>

      <ScrollView contentContainerStyle={s.scroll} showsVerticalScrollIndicator={false}>

        {/* Global score ring */}
        <View style={s.globalCard}>
          <RingChart size={80} progress={globalScore / 100} color={colors.green} label={String(globalScore)} />
          <View style={{ flex: 1, marginLeft: spacing.md }}>
            <Text style={[s.globalLabel, { color: colors.green }]}>{GLOBAL.label}</Text>
            <Text style={s.globalRank}>{GLOBAL.rank}</Text>
            <View style={s.top20}>
              <Text style={s.top20Text}>Top 20%</Text>
            </View>
          </View>
        </View>

        {/* 5 component scores */}
        <SectionLabel style={s.gap}>5 composantes · Nb05</SectionLabel>
        <View style={s.compCard}>
          {COMPONENTS.map((c, i) => (
            <ScoreRow key={i} label={c.label} score={c.score} color={c.color} />
          ))}
        </View>

        {/* Weekly chart */}
        <SectionLabel style={s.gap}>Visites / jour · S15</SectionLabel>
        <View style={s.chartCard}>
          <MiniBarChart data={WEEKLY_BARS} />
          <View style={s.chartLegend}>
            {['L','M','M','J','V','S','D'].map((d, i) => (
              <Text key={i} style={s.chartDay}>{d}</Text>
            ))}
          </View>
        </View>

        {/* 4-metric grid */}
        <View style={s.metricsGrid}>
          {metrics.map((m, i) => (
            <View key={i} style={s.metricTile}>
              <Text style={[s.metricVal, { color: m.color }]}>{m.value}</Text>
              <Text style={s.metricLabel}>{m.label}</Text>
              <Text style={[s.metricDelta, { color: m.up ? colors.green : colors.red }]}>
                {m.delta}
              </Text>
            </View>
          ))}
        </View>

        {/* Prime section */}
        <SectionLabel style={s.gap}>Primes & objectifs · Nb05</SectionLabel>
        <View style={s.primeRow}>
          <View style={s.primeTile}>
            <Text style={[s.primeVal, { color: colors.gold }]}>3 200€</Text>
            <Text style={s.primeLabel}>Prime S15</Text>
          </View>
          <View style={[s.primeTile, { marginLeft: spacing.sm }]}>
            <Text style={[s.primeVal, { color: colors.green }]}>+18%</Text>
            <Text style={s.primeLabel}>vs Objectif</Text>
          </View>
        </View>

        {/* Agent actions */}
        <SectionLabel style={s.gap}>Actions suggérées · Agent Nb05</SectionLabel>
        <View style={s.actionsCard}>
          {ACTIONS.map((a, i) => (
            <ActionItem key={i} num={a.num} text={a.text} />
          ))}
        </View>

        {/* NLP signal tip */}
        <View style={[s.tipCard, { backgroundColor: colors.purpleB, borderColor: colors.purpleE }]}>
          <Text style={s.tipLabel}>Action Nb05 prédictif</Text>
          <Text style={s.tipText}>Améliorer signaux NLP → +0.3 pts score prédit dès la prochaine période.</Text>
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  safe:         { flex: 1, backgroundColor: colors.s1 },
  header:       { padding: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.bd },
  title:        { fontSize: 15, fontWeight: '800', color: colors.t1, letterSpacing: -0.3 },
  sub:          { fontSize: 9, color: colors.t2, marginTop: 2 },
  scroll:       { padding: spacing.md, paddingBottom: 32 },

  globalCard:   { backgroundColor: colors.s2, borderColor: colors.bd, borderWidth: 1, borderRadius: radius.sm, padding: spacing.md, flexDirection: 'row', alignItems: 'center', marginBottom: spacing.sm },
  globalLabel:  { fontSize: 18, fontWeight: '900', letterSpacing: -0.4 },
  globalRank:   { fontSize: 8, color: colors.t2, marginTop: 3 },
  top20:        { marginTop: 6, backgroundColor: colors.greenB, borderColor: colors.greenE, borderWidth: 1, borderRadius: 99, paddingHorizontal: 8, paddingVertical: 2, alignSelf: 'flex-start' },
  top20Text:    { fontSize: 9, fontWeight: '700', color: colors.green },

  gap:          { marginTop: spacing.md, marginBottom: spacing.xs },

  compCard:     { backgroundColor: colors.s2, borderColor: colors.bd, borderWidth: 1, borderRadius: radius.sm, padding: spacing.sm },

  chartCard:    { backgroundColor: colors.s2, borderColor: colors.bd, borderWidth: 1, borderRadius: radius.sm, padding: spacing.sm },
  chartLegend:  { flexDirection: 'row', justifyContent: 'space-around', marginTop: 4 },
  chartDay:     { fontSize: 7, color: colors.t3, textAlign: 'center', flex: 1 },

  metricsGrid:  { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: spacing.sm },
  metricTile:   { backgroundColor: colors.s2, borderColor: colors.bd, borderWidth: 1, borderRadius: radius.sm, padding: spacing.sm, width: '48%' },
  metricVal:    { fontSize: 18, fontWeight: '900', letterSpacing: -0.4 },
  metricLabel:  { fontSize: 8, color: colors.t2, marginTop: 1 },
  metricDelta:  { fontSize: 8, fontWeight: '600', marginTop: 2 },

  primeRow:     { flexDirection: 'row' },
  primeTile:    { flex: 1, backgroundColor: colors.s2, borderColor: colors.bd, borderWidth: 1, borderRadius: radius.sm, padding: spacing.sm },
  primeVal:     { fontSize: 16, fontWeight: '900', letterSpacing: -0.3 },
  primeLabel:   { fontSize: 8, color: colors.t2, marginTop: 1 },

  actionsCard:  { backgroundColor: colors.s2, borderColor: colors.bd, borderWidth: 1, borderRadius: radius.sm, paddingHorizontal: spacing.sm },

  tipCard:      { marginTop: spacing.sm, padding: spacing.sm, borderRadius: radius.sm, borderWidth: 1 },
  tipLabel:     { fontSize: 8, fontWeight: '700', color: colors.purple, marginBottom: 3 },
  tipText:      { fontSize: 9, color: colors.t2, lineHeight: 14 },
});
