// ─── Screen 2: Brief pré-visite ──────────────────────────────────────────────
// Notebooks: Nb04 (Gemini brief), Nb09 (Rx score), Nb11 (quality tier), Nb12 (16 NLP flags)
import React from 'react';
import { View, Text, ScrollView, StyleSheet, SafeAreaView, TouchableOpacity } from 'react-native';
import { colors, spacing, radius } from '../theme';
import { RingChart, FlagsRow, SectionLabel } from '../components';

// ─── Data ────────────────────────────────────────────────────────────────────
const DOCTOR = {
  initials: 'DR',
  name:     'Dr Rousseau',
  spec:     'Cardiologue · CHU Bordeaux',
  tier:     'Tier A',
};

const SENTIMENT = {
  score: 0.78,
  label: 'Sentiment positif · CamemBERT Nb12',
  sub:   '3 visites analysées · Conf. 87% · Acc≈0.60',
};

// All 16 flags from MultiOutputClassifier · Nb12
const FLAGS = [
  { label: 'Prix sensible',      variant: 'red'    },
  { label: 'Concurrent cité',    variant: 'orange' },
  { label: 'Études cliniques',   variant: 'blue'   },
  { label: 'Cardixol 10mg',      variant: 'purple' },
  { label: 'Intérêt élevé',      variant: 'green'  },
  { label: 'Renouvellement',     variant: 'teal'   },
  { label: 'Ordonnance habituel',variant: 'blue'   },
  { label: 'Demande stock',      variant: 'orange' },
];

const OBJECTIONS = [
  '"Le générique coûte moitié moins cher"',
  'Demande données comparatives récentes',
];

const QUALITY = { tier: 'A', score: 0.82, model: 'RF AUC=0.984 · Nb11' };

const GEMINI_BRIEF = 'Mettre en avant CARDIOX-2024. Préparer slide ROI patient. Cible : +2 Rx Cardixol 10mg.';

// ─── Component ────────────────────────────────────────────────────────────────
export default function BriefScreen({ navigation }) {
  return (
    <SafeAreaView style={s.safe}>
      {/* Doctor header */}
      <View style={s.docHeader}>
        <View style={s.avatar}>
          <Text style={s.avatarText}>{DOCTOR.initials}</Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={s.docName}>{DOCTOR.name}</Text>
          <Text style={s.docSpec}>{DOCTOR.spec}</Text>
        </View>
        <View style={s.tierPill}>
          <Text style={s.tierText}>{DOCTOR.tier}</Text>
        </View>
      </View>

      <ScrollView contentContainerStyle={s.scroll} showsVerticalScrollIndicator={false}>

        {/* Sentiment — Nb12 */}
        <View style={[s.sentCard, { backgroundColor: colors.greenB, borderColor: colors.greenE }]}>
          <Text style={{ fontSize: 22 }}>😊</Text>
          <View style={{ flex: 1, marginLeft: spacing.sm }}>
            <Text style={[s.sentLabel, { color: colors.green }]}>{SENTIMENT.label}</Text>
            <Text style={s.sentSub}>{SENTIMENT.sub}</Text>
          </View>
          <Text style={[s.sentScore, { color: colors.green }]}>{SENTIMENT.score}</Text>
        </View>

        {/* 16 NLP Flags — Nb12 */}
        <SectionLabel style={s.gap}>16 flags NLP · MultiLabel Nb12</SectionLabel>
        <FlagsRow flags={FLAGS} />

        {/* Visit quality tier — Nb11 */}
        <SectionLabel style={s.gap}>Qualité visite prédite · Nb11</SectionLabel>
        <View style={[s.qualCard, { backgroundColor: colors.blueB, borderColor: colors.blueE }]}>
          <RingChart size={56} progress={0.82} color={colors.blue} label="A" />
          <View style={{ flex: 1, marginLeft: spacing.md }}>
            <Text style={s.qualTitle}>Tier A · Score ≥ 0.82</Text>
            <Text style={s.qualSub}>{QUALITY.model}</Text>
            <Text style={[s.qualInfo, { color: colors.blue }]}>Visite à fort impact attendu</Text>
          </View>
        </View>

        {/* Objections */}
        <SectionLabel style={s.gap}>Objections anticipées</SectionLabel>
        <View style={s.objCard}>
          {OBJECTIONS.map((o, i) => (
            <View key={i} style={[s.objRow, i === OBJECTIONS.length - 1 && { borderBottomWidth: 0 }]}>
              <View style={s.objDot} />
              <Text style={s.objText}>{o}</Text>
            </View>
          ))}
        </View>

        {/* Gemini brief — Nb04 */}
        <SectionLabel style={s.gap}>Brief Gemini · Nb04</SectionLabel>
        <View style={[s.geminiCard, { backgroundColor: colors.purpleB, borderColor: colors.purpleE }]}>
          <Text style={s.geminiText}>
            {GEMINI_BRIEF.replace('+2 Rx Cardixol 10mg', '')}
            <Text style={{ color: colors.green, fontWeight: '700' }}>+2 Rx Cardixol 10mg</Text>
          </Text>
        </View>

        {/* CTA */}
        <TouchableOpacity
          style={s.cta}
          onPress={() => navigation.navigate('Saisie')}
          activeOpacity={0.85}
        >
          <Text style={s.ctaText}>▶  Démarrer la visite</Text>
        </TouchableOpacity>

      </ScrollView>
    </SafeAreaView>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  safe:       { flex: 1, backgroundColor: colors.s1 },
  docHeader:  { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, padding: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.bd },
  avatar:     { width: 36, height: 36, borderRadius: 18, backgroundColor: colors.purpleB, borderWidth: 1, borderColor: colors.purpleE, alignItems: 'center', justifyContent: 'center' },
  avatarText: { fontSize: 9, fontWeight: '900', color: colors.purple },
  docName:    { fontSize: 13, fontWeight: '800', color: colors.t1, letterSpacing: -0.3 },
  docSpec:    { fontSize: 8, color: colors.t2, marginTop: 1 },
  tierPill:   { backgroundColor: colors.purpleB, borderColor: colors.purpleE, borderWidth: 1, borderRadius: 99, paddingHorizontal: 8, paddingVertical: 3 },
  tierText:   { fontSize: 9, fontWeight: '700', color: colors.purple },
  scroll:     { padding: spacing.md, paddingBottom: 32 },
  sentCard:   { flexDirection: 'row', alignItems: 'center', padding: spacing.sm, borderRadius: radius.sm, borderWidth: 1, marginBottom: spacing.sm },
  sentLabel:  { fontSize: 9, fontWeight: '700' },
  sentSub:    { fontSize: 8, color: colors.greenE, marginTop: 1 },
  sentScore:  { fontSize: 18, fontWeight: '900' },
  gap:        { marginTop: spacing.md, marginBottom: spacing.xs },
  qualCard:   { flexDirection: 'row', alignItems: 'center', padding: spacing.sm, borderRadius: radius.sm, borderWidth: 1, marginBottom: spacing.sm },
  qualTitle:  { fontSize: 11, fontWeight: '700', color: colors.t1 },
  qualSub:    { fontSize: 8, color: colors.t2, marginTop: 2 },
  qualInfo:   { fontSize: 8, marginTop: 2 },
  objCard:    { backgroundColor: colors.s2, borderColor: colors.bd, borderWidth: 1, borderRadius: radius.sm, paddingHorizontal: spacing.sm, overflow: 'hidden' },
  objRow:     { flexDirection: 'row', alignItems: 'flex-start', gap: 6, paddingVertical: 6, borderBottomWidth: 1, borderBottomColor: colors.bd },
  objDot:     { width: 4, height: 4, borderRadius: 2, backgroundColor: colors.red, marginTop: 4, flexShrink: 0 },
  objText:    { fontSize: 9, color: colors.t2, flex: 1, lineHeight: 14 },
  geminiCard: { padding: spacing.sm, borderRadius: radius.sm, borderWidth: 1, marginBottom: spacing.md },
  geminiText: { fontSize: 9, color: colors.t2, lineHeight: 15 },
  cta:        { backgroundColor: colors.blue, borderRadius: radius.sm, paddingVertical: 12, alignItems: 'center' },
  ctaText:    { fontSize: 13, fontWeight: '700', color: '#fff', letterSpacing: -0.2 },
});
