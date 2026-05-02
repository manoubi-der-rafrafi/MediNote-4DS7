// ─── HistoriqueVisitesScreen.js — Historique & Qualité Visites ────────────────
// Sources: Nb11 (RF AUC=0.984 Tier A/B/C/D), Nb05 (score délégué), Nb12 (NLP)
import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView,
  TouchableOpacity, SafeAreaView,
} from 'react-native';
import { colors, spacing, radius, font } from '../theme';
import {
  RingChart, SectionLabel, Card, Pill, KpiTile,
  VisitRow, MiniSparkline, AlertStrip,
} from '../components/medecin';

// ── Data ──────────────────────────────────────────────────────────────────────
const TIER_COLOR = {
  A: colors.teal,
  B: colors.blue,
  C: colors.orange,
  D: colors.red,
};

const VISITS = [
  { date: '05/04/26', tier: 'A', quality: 'Visite excellente · 3 produits',   score: 94, color: colors.teal   },
  { date: '28/03/26', tier: 'A', quality: 'Bonne visite · brief respecté',    score: 88, color: colors.teal   },
  { date: '14/03/26', tier: 'B', quality: 'Visite correcte · 1 objection',    score: 72, color: colors.blue   },
  { date: '01/03/26', tier: 'A', quality: 'Excellente · NPS élevé',           score: 96, color: colors.teal   },
  { date: '18/02/26', tier: 'B', quality: 'Courte · médecin pressé',          score: 65, color: colors.blue   },
  { date: '05/02/26', tier: 'C', quality: 'Difficile · Rx en baisse',         score: 51, color: colors.orange },
  { date: '22/01/26', tier: 'A', quality: 'Top · Cardiomax accepté',          score: 91, color: colors.teal   },
];

const SCORE_TREND = [65, 72, 51, 88, 96, 72, 94];

const TIER_DIST = [
  { tier: 'A', count: 4, pct: 57, color: colors.teal   },
  { tier: 'B', count: 2, pct: 29, color: colors.blue   },
  { tier: 'C', count: 1, pct: 14, color: colors.orange },
  { tier: 'D', count: 0, pct: 0,  color: colors.red    },
];

const KPIS = [
  { label: 'Score moy',    value: '79.7', color: colors.teal   },
  { label: 'Tier A',       value: '57%',  color: colors.green  },
  { label: 'Durée moy',    value: '18 min', color: colors.blue },
  { label: 'Rx générées',  value: '31',   color: colors.purple },
];

const INSIGHTS = [
  { icon: '📈', text: 'Score en hausse de +14 pts sur 30 jours · Nb11', color: colors.green },
  { icon: '🎯', text: '57% des visites en Tier A (objectif 50%) · Nb11 AUC=0.984', color: colors.teal },
  { icon: '💊', text: 'Cardiomax Rx +34% vs Q4 · Nb09', color: colors.blue },
  { icon: '⚠️', text: '1 visite Tier C le 05/02 — analyser les objections', color: colors.orange },
];

export default function HistoriqueVisitesScreen({ navigation }) {
  const [activeFilter, setActiveFilter] = useState('Tous');
  const filters = ['Tous', 'Tier A', 'Tier B', 'Tier C'];

  const filtered = activeFilter === 'Tous'
    ? VISITS
    : VISITS.filter(v => `Tier ${v.tier}` === activeFilter);

  return (
    <SafeAreaView style={s.safe}>
      <ScrollView style={s.scroll} contentContainerStyle={s.content} showsVerticalScrollIndicator={false}>

        {/* ── Page title ── */}
        <View style={s.titleRow}>
          {navigation && (
            <TouchableOpacity onPress={() => navigation.goBack()} style={s.backBtn}>
              <Text style={s.backTxt}>← Retour</Text>
            </TouchableOpacity>
          )}
          <Text style={s.pageTitle}>Historique Visites</Text>
          <Text style={s.pageSub}>Dr. Amina Bensalem · Nb11 RF AUC=0.984</Text>
        </View>

        {/* ── KPIs ── */}
        <View style={s.kpiRow}>
          {KPIS.map((k, i) => <KpiTile key={i} {...k} style={i < KPIS.length - 1 ? { marginRight: spacing.xs } : {}} />)}
        </View>

        {/* ── Qualité globale ring ── */}
        <SectionLabel title="Qualité globale" tag="Nb11 · Modèle RF" />
        <Card style={{ flexDirection: 'row', alignItems: 'center', gap: spacing.xl }}>
          <RingChart size={88} progress={0.797} color={colors.teal} label="79.7" sublabel="/ 100" />
          <View style={{ flex: 1 }}>
            <Text style={s.ringTitle}>Score qualité visite</Text>
            <Text style={s.ringSub}>Random Forest entraîné sur 12 critères NLP + durée + détailing · Nb11</Text>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: spacing.sm }}>
              <MiniSparkline data={SCORE_TREND} color={colors.teal} width={72} height={24} />
              <Text style={{ color: colors.green, fontSize: font.sm, fontWeight: '700' }}>+14 pts ↑</Text>
            </View>
          </View>
        </Card>

        {/* ── Tier distribution ── */}
        <SectionLabel title="Distribution Tiers" tag="7 visites · 3 mois" />
        <Card>
          <View style={{ flexDirection: 'row', gap: spacing.sm }}>
            {TIER_DIST.map((t, i) => (
              <View key={i} style={[s.tierBox, { borderColor: t.color + '50', backgroundColor: t.color + '12' }]}>
                <Text style={[s.tierLetter, { color: t.color }]}>Tier {t.tier}</Text>
                <Text style={[s.tierCount, { color: t.color }]}>{t.count}</Text>
                <Text style={s.tierPct}>{t.pct}%</Text>
              </View>
            ))}
          </View>
          {/* Bar ── */}
          <View style={{ height: 6, borderRadius: radius.full, flexDirection: 'row', overflow: 'hidden', marginTop: spacing.md }}>
            {TIER_DIST.filter(t => t.pct > 0).map((t, i) => (
              <View key={i} style={{ width: `${t.pct}%`, backgroundColor: t.color }} />
            ))}
          </View>
        </Card>

        {/* ── Insights ── */}
        <SectionLabel title="Insights IA" tag="Agent Coaching" />
        {INSIGHTS.map((ins, i) => (
          <View key={i} style={[s.insightRow, { borderLeftColor: ins.color }]}>
            <Text style={s.insightIcon}>{ins.icon}</Text>
            <Text style={[s.insightText, { color: ins.color }]}>{ins.text}</Text>
          </View>
        ))}

        {/* ── Filters ── */}
        <SectionLabel title="Liste des visites" tag={`${filtered.length} résultats`} />
        <View style={s.filterRow}>
          {filters.map(f => (
            <TouchableOpacity
              key={f}
              onPress={() => setActiveFilter(f)}
              style={[s.filterBtn, activeFilter === f && s.filterActive]}
            >
              <Text style={[s.filterTxt, activeFilter === f && { color: colors.teal }]}>{f}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* ── Visit list ── */}
        <Card>
          {filtered.map((v, i) => (
            <VisitRow key={i} date={v.date} tier={v.tier} quality={v.quality} score={v.score} color={v.color} />
          ))}
        </Card>

        {/* ── CTA ── */}
        <TouchableOpacity style={s.cta} onPress={() => navigation && navigation.navigate('ProfilMedecin')}>
          <Text style={s.ctaTxt}>👤  Retour profil médecin</Text>
        </TouchableOpacity>

        <View style={{ height: spacing.xxl }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe:         { flex: 1, backgroundColor: colors.bg },
  scroll:       { flex: 1 },
  content:      { padding: spacing.lg },
  titleRow:     { marginBottom: spacing.lg },
  backBtn:      { marginBottom: spacing.sm },
  backTxt:      { color: colors.teal, fontSize: font.sm, fontWeight: '600' },
  pageTitle:    { color: colors.t1, fontSize: font.xl, fontWeight: '800' },
  pageSub:      { color: colors.t3, fontSize: font.sm, marginTop: 2 },
  kpiRow:       { flexDirection: 'row', marginBottom: spacing.sm },
  ringTitle:    { color: colors.t1, fontSize: font.base, fontWeight: '700' },
  ringSub:      { color: colors.t2, fontSize: font.sm, marginTop: 4, lineHeight: 18 },
  tierBox:      { flex: 1, borderRadius: radius.md, borderWidth: 1, padding: spacing.sm, alignItems: 'center' },
  tierLetter:   { fontSize: font.xs, fontWeight: '700' },
  tierCount:    { fontSize: font.xxl, fontWeight: '800', marginTop: 2 },
  tierPct:      { fontSize: font.xs, color: colors.t3 },
  insightRow:   { backgroundColor: colors.s1, borderRadius: radius.md, borderLeftWidth: 3, padding: spacing.md, marginBottom: spacing.sm, flexDirection: 'row', alignItems: 'flex-start', gap: spacing.sm },
  insightIcon:  { fontSize: font.lg },
  insightText:  { fontSize: font.sm, flex: 1, lineHeight: 18, fontWeight: '600' },
  filterRow:    { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.md },
  filterBtn:    { paddingHorizontal: spacing.md, paddingVertical: spacing.xs, borderRadius: radius.full, backgroundColor: colors.s2, borderWidth: 1, borderColor: colors.bd },
  filterActive: { borderColor: colors.teal, backgroundColor: colors.tealB },
  filterTxt:    { color: colors.t2, fontSize: font.sm, fontWeight: '600' },
  cta:          { backgroundColor: colors.teal, borderRadius: radius.lg, paddingVertical: 14, alignItems: 'center', marginTop: spacing.sm },
  ctaTxt:       { color: colors.bg, fontSize: font.base, fontWeight: '700' },
});
