// ─── Screen 1: Feed du matin ─────────────────────────────────────────────────
// Notebooks: Nb05 (score délégué), Nb06 (NBA/geo), Nb07 (lot péremption), Nb09 (Rx prediction)
import React, { useContext } from 'react';
import { View, Text, ScrollView, StyleSheet, SafeAreaView } from 'react-native';
import { colors, spacing, radius } from '../theme';
import { SessionContext } from '../context/SessionContext';
import {
  RingChart, KpiTile, DoctorRow, AlertStrip, SectionLabel,
} from '../components';
import DelegateHeader from '../components/DelegateHeader';
import { useDelegateData } from '../hooks/useDelegateData';

const NBA_LIST = [
  { initials: 'DR', name: 'Dr Rousseau', sub: 'Cardio · Score Rx 0.91 · Tier A · 14h30', pill: 'P1', pv: 'red',    ab: colors.redB,    ac: colors.red    },
  { initials: 'MB', name: 'Dr Mbaye',    sub: 'Géné · Score Rx 0.74 · Tier B · 15h15',  pill: 'P2', pv: 'orange', ab: colors.orangeB, ac: colors.orange },
  { initials: 'LF', name: 'Dr Lefebvre', sub: 'Cardio · Score Rx 0.61 · Tier B · 16h00',pill: 'P3', pv: 'green',  ab: colors.greenB,  ac: colors.green  },
];

// ─── Component ────────────────────────────────────────────────────────────────
export default function FeedScreen({ navigation }) {
  // Safe access to session context to avoid crashes if provider is missing
  const session = useContext(SessionContext) || {};
  const currentDelegate = session.currentDelegate;
  const delegateId = currentDelegate?.id_deleg ?? 541;
  const { scorecard, loading: apiLoading } = useDelegateData(delegateId);

  const KPI = [
    {
      value: scorecard?.visits_today != null
        ? `${scorecard.visits_today}/${scorecard.visits_target ?? 12}`
        : '8/12',
      label: 'Visites jour',
      delta: '↑ NBA Nb06',
      up: true,
      color: colors.blue,
    },
    {
      value: scorecard?.ca_achievement_pct != null
        ? `${Math.round(scorecard.ca_achievement_pct)}%`
        : '84%',
      label: 'Objectif',
      delta: '↓ −3pts',
      up: false,
      color: colors.purple,
    },
  ];

  const delegateName = currentDelegate?.nom?.split(' ').pop() || 'Délégué';
  const delegateScore = currentDelegate?.score / 100 || 0.84;

  return (
    <SafeAreaView style={s.safe}>
      {/* Delegate Session Header */}
      <DelegateHeader />

      {/* Screen Header */}
      <View style={s.header}>
        <View>
          <Text style={s.headerTitle}>Bonjour {delegateName} 👋</Text>
          <Text style={s.headerSub}>
            Jeu. 9 avril · Score délégué{' '}
            <Text style={{ color: colors.green, fontWeight: '800' }}>{delegateScore.toFixed(2)}</Text>
            {' · Nb05 — '}<Text style={{ color: currentDelegate?.color }}>{currentDelegate?.tier}</Text>
          </Text>
        </View>
      </View>

      <ScrollView contentContainerStyle={s.scroll} showsVerticalScrollIndicator={false}>

        {/* KPI strip */}
        <View style={s.kpiRow}>
          {KPI.map((k, i) => (
            <KpiTile
              key={i}
              value={k.value}
              label={k.label}
              delta={k.delta}
              deltaUp={k.up}
              color={k.color}
              style={{ marginLeft: i > 0 ? spacing.sm : 0 }}
            />
          ))}
        </View>

        {/* Rx Prediction — Nb09 */}
        <View style={[s.predCard, { backgroundColor: colors.greenB, borderColor: colors.greenE }]}>
          <Text style={s.predLabel}>Prédiction Rx · Nb09 — AUC 1.0</Text>
          <View style={s.predRow}>
            <RingChart size={76} progress={0.82} color={colors.green} label="82%" />
            <View style={{ flex: 1, marginLeft: spacing.md }}>
              <Text style={s.predTitle}>Prob. forte prescription</Text>
              <Text style={s.predDesc}>Visite suivante · top 3 médecins P1</Text>
              <View style={s.tagRow}>
                {['RF', 'GB', 'LR'].map(t => (
                  <View key={t} style={s.modelTag}>
                    <Text style={s.modelTagText}>{t}</Text>
                  </View>
                ))}
              </View>
            </View>
          </View>
        </View>

        {/* NBA list — Nb06 */}
        <SectionLabel style={s.sectionGap}>NBA du jour · Agent Nb06</SectionLabel>
        {NBA_LIST.map((d, i) => (
          <View key={i} style={{ marginBottom: spacing.xs }}>
            <DoctorRow
              initials={d.initials}
              name={d.name}
              sub={d.sub}
              pillLabel={d.pill}
              pillVariant={d.pv}
              avatarBg={d.ab}
              avatarColor={d.ac}
              onPress={() => navigation.navigate('Brief', { doctor: d })}
            />
          </View>
        ))}

        {/* Lot alert — Nb07 */}
        <View style={{ marginTop: spacing.xs }}>
          <AlertStrip
            icon="⚠️"
            title="Rappel lot — Cardixol 5mg · Nb07"
            desc="Lot #CX22-A · 18 pharmacies à informer · CRITICAL"
            bg={colors.goldB}
            border={colors.goldE}
            titleColor={colors.gold}
          />
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  safe:        { flex: 1, backgroundColor: colors.s1 },
  header:      { paddingHorizontal: spacing.lg, paddingTop: spacing.lg, paddingBottom: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.bd },
  headerTitle: { fontSize: 15, fontWeight: '800', color: colors.t1, letterSpacing: -0.3 },
  headerSub:   { fontSize: 9, color: colors.t2, marginTop: 2 },
  scroll:      { padding: spacing.md, paddingBottom: spacing.xl },
  kpiRow:      { flexDirection: 'row', marginBottom: spacing.sm },
  predCard:    { borderWidth: 1, borderRadius: radius.sm, padding: spacing.md, marginBottom: spacing.sm },
  predLabel:   { fontSize: 8, fontWeight: '700', color: colors.green, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: spacing.xs },
  predRow:     { flexDirection: 'row', alignItems: 'center' },
  predTitle:   { fontSize: 12, fontWeight: '700', color: colors.t1 },
  predDesc:    { fontSize: 8, color: colors.t2, marginTop: 2 },
  tagRow:      { flexDirection: 'row', gap: 4, marginTop: 6 },
  modelTag:    { backgroundColor: colors.s3, borderRadius: 4, paddingHorizontal: 5, paddingVertical: 2 },
  modelTagText:{ fontSize: 8, fontWeight: '700', color: colors.t3 },
  sectionGap:  { marginTop: spacing.xs, marginBottom: spacing.xs },
});
