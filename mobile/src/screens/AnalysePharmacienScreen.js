// ─── AnalysePharmacienScreen.js — Analyse Opportunités + Tier Eligibilité ─────
// Sources: Nb11 (Tier eligibility RF AUC=0.984), Nb04 (Gemini analysis), Nb03 (segmentation)
import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView,
  TouchableOpacity, SafeAreaView,
} from 'react-native';
import { colors, spacing, radius, font } from '../theme';
import {
  RingChart, SectionLabel, Card, Pill, KpiTile,
  SegmentBadge, ProgressBar, MiniSparkline, ActionItem,
} from '../components/pharmacie';
import { usePharmacyData } from '../hooks/usePharmacyData';

// ── Data ──────────────────────────────────────────────────────────────────────
const KPIS = [
  { label: 'CA pharmacie',  value: '312k',  color: colors.gold   },
  { label: 'Croissance',    value: '+18%',  color: colors.green  },
  { label: 'Nb produits',   value: '24',    color: colors.blue   },
  { label: 'Part de marché', value: '7.2%', color: colors.teal   },
];

const PRODUCTS_GEMINI = [
  { name: 'Cardiomax 10mg',  ca: '87k MAD', trend: [40, 55, 62, 58, 71, 78, 87], color: colors.gold,   badge: 'TOP VENTE · Nb04' },
  { name: 'Vasorel Plus',    ca: '64k MAD', trend: [30, 34, 38, 42, 49, 55, 64], color: colors.teal,   badge: 'Croissance +34%' },
  { name: 'Hypertensol 5mg', ca: '51k MAD', trend: [60, 55, 52, 50, 48, 51, 51], color: colors.orange, badge: 'Stagnation détectée' },
  { name: 'Diuremax 40mg',   ca: '38k MAD', trend: [20, 25, 28, 31, 34, 36, 38], color: colors.blue,   badge: 'Montée progressive' },
  { name: 'Cholestop Plus',  ca: '29k MAD', trend: [28, 27, 26, 28, 29, 28, 29], color: colors.purple, badge: 'Stable' },
];

const TIER_CRITERIA = [
  { label: 'CA mensuel',         value: 312, max: 350, color: colors.gold,   unit: 'k' },
  { label: 'Fidélité produits',  value: 89,  max: 100, color: colors.teal,   unit: '%' },
  { label: 'Réactivité alertes', value: 92,  max: 100, color: colors.green,  unit: '%' },
  { label: 'NPS pharmacien',     value: 78,  max: 100, color: colors.blue,   unit: '%' },
];

const ANIMATIONS = [
  { icon: '🎯', title: 'Animation Cardiomax Q2 2026',       sub: 'Prévu 22/04 · ROI estimé +28k MAD · Agent Marketing', color: colors.gold   },
  { icon: '🔬', title: 'Formation Vasorel Plus — protocole', sub: '5 pharmaciens · Nb04 brief technique Gemini',         color: colors.teal   },
  { icon: '📦', title: 'Offre bundle ADVOCATE exclusive',    sub: 'Nb03 segment · −12% sur commande > 50k',              color: colors.purple },
];

const INSIGHTS = [
  { icon: '⭐', text: 'Éligible Tier A renouvellement · Nb11 RF AUC=0.984 · Score 89/100', color: colors.teal   },
  { icon: '📈', text: 'CA en hausse +18% vs N-1 · potentiel 350k si Hypertensol stabilisé', color: colors.gold   },
  { icon: '💡', text: 'Gemini recommande focus Vasorel Plus pour atteindre +34% CA · Nb04', color: colors.blue   },
  { icon: '⚠️', text: 'Hypertensol en stagnation — intervention technique recommandée',      color: colors.orange },
];

export default function AnalysePharmacienScreen({ navigation }) {
  const [expandedProd, setExpandedProd] = useState(null);
  const { financial, performance, loading: apiLoading } = usePharmacyData(123);

  const KPIS_LIVE = [
    {
      ...KPIS[0],
      value: financial?.campaign_roi != null
        ? `${Math.round(financial.campaign_roi)}k` : KPIS[0].value,
    },
    {
      ...KPIS[1],
      value: performance?.rx_growth != null
        ? `+${performance.rx_growth.toFixed(0)}%` : KPIS[1].value,
    },
    ...KPIS.slice(2),
  ];

  return (
    <SafeAreaView style={s.safe}>
      <ScrollView style={s.scroll} contentContainerStyle={s.content} showsVerticalScrollIndicator={false}>

        {/* ── Header ── */}
        <View style={s.titleRow}>
          {navigation && (
            <TouchableOpacity onPress={() => navigation.goBack()} style={s.backBtn}>
              <Text style={s.backTxt}>← Alertes stock</Text>
            </TouchableOpacity>
          )}
          <Text style={s.pageTitle}>Analyse & Opportunités</Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: spacing.xs }}>
            <Text style={s.pageSub}>Pharmacie Al Amal · Rabat</Text>
            <SegmentBadge segment="ADVOCATE" />
          </View>
        </View>

        {/* ── KPIs ── */}
        <View style={s.kpiRow}>
          {KPIS_LIVE.map((k, i) => <KpiTile key={i} {...k} style={i < KPIS_LIVE.length - 1 ? { marginRight: spacing.xs } : {}} />)}
        </View>

        {/* ── Tier A eligibility ring (Nb11) ── */}
        <SectionLabel title="Éligibilité Tier A" tag="Nb11 · RF AUC = 0.984" />
        <Card style={{ flexDirection: 'row', alignItems: 'center', gap: spacing.xl }}>
          <RingChart size={88} progress={0.89} color={colors.teal} label="89%" sublabel="Tier A" />
          <View style={{ flex: 1 }}>
            <Text style={s.tierTitle}>Score d'éligibilité Tier A</Text>
            <Text style={s.tierSub}>Random Forest · 4 critères · Renouvellement trimestriel · Nb11</Text>
            <Pill label="✓ Tier A confirmé" color={colors.teal} />
          </View>
        </Card>

        {/* ── Tier criteria breakdown ── */}
        <Card>
          {TIER_CRITERIA.map((c, i) => (
            <ProgressBar key={i} label={c.label} value={c.value} max={c.max} color={c.color} unit={c.unit} />
          ))}
        </Card>

        {/* ── Insights ── */}
        <SectionLabel title="Insights IA" tag="Nb04 · Nb11 · Nb03" />
        {INSIGHTS.map((ins, i) => (
          <View key={i} style={[s.insightRow, { borderLeftColor: ins.color }]}>
            <Text style={s.insightIcon}>{ins.icon}</Text>
            <Text style={[s.insightText, { color: ins.color }]}>{ins.text}</Text>
          </View>
        ))}

        {/* ── Analyse produits Gemini (Nb04) ── */}
        <SectionLabel title="Performance produits" tag="Nb04 · Gemini AI" />
        {PRODUCTS_GEMINI.map((p, i) => (
          <TouchableOpacity key={i} onPress={() => setExpandedProd(expandedProd === i ? null : i)}>
            <Card style={{ marginBottom: spacing.sm }}>
              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <View style={{ flex: 1 }}>
                  <Text style={{ color: colors.t1, fontSize: font.base, fontWeight: '700' }}>{p.name}</Text>
                  <Pill label={p.badge} color={p.color} />
                </View>
                <View style={{ alignItems: 'flex-end', gap: spacing.xs }}>
                  <MiniSparkline data={p.trend} color={p.color} width={64} height={22} />
                  <Text style={{ color: p.color, fontSize: font.base, fontWeight: '800' }}>{p.ca}</Text>
                </View>
              </View>
              {expandedProd === i && (
                <View style={{ marginTop: spacing.md, paddingTop: spacing.md, borderTopWidth: 1, borderTopColor: colors.bd }}>
                  <Text style={{ color: colors.t2, fontSize: font.sm, lineHeight: 18 }}>
                    Analyse Gemini Nb04 : Performance {p.name} en hausse sur les 7 derniers mois.
                    Recommandation agent : renforcer la présence en rayon et proposer une animation
                    pour maximiser le potentiel de croissance. Score Nb11 Tier A confirmé pour ce produit.
                  </Text>
                </View>
              )}
            </Card>
          </TouchableOpacity>
        ))}

        {/* ── Animations ── */}
        <SectionLabel title="Animations planifiées" tag="Agent Marketing" />
        <Card>
          {ANIMATIONS.map((a, i) => <ActionItem key={i} {...a} />)}
        </Card>

        {/* ── CTA ── */}
        <TouchableOpacity style={s.cta} onPress={() => navigation && navigation.navigate('AlertesStock')}>
          <Text style={s.ctaTxt}>🔔  Voir alertes expiry</Text>
        </TouchableOpacity>

        <View style={{ height: spacing.xxl }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe:        { flex: 1, backgroundColor: colors.bg },
  scroll:      { flex: 1 },
  content:     { padding: spacing.lg },
  titleRow:    { marginBottom: spacing.lg },
  backBtn:     { marginBottom: spacing.sm },
  backTxt:     { color: colors.gold, fontSize: font.sm, fontWeight: '600' },
  pageTitle:   { color: colors.t1, fontSize: font.xl, fontWeight: '800' },
  pageSub:     { color: colors.t3, fontSize: font.sm },
  kpiRow:      { flexDirection: 'row', marginBottom: spacing.sm },
  tierTitle:   { color: colors.t1, fontSize: font.base, fontWeight: '700', marginBottom: spacing.xs },
  tierSub:     { color: colors.t2, fontSize: font.sm, lineHeight: 18, marginBottom: spacing.sm },
  insightRow:  { backgroundColor: colors.s1, borderRadius: radius.md, borderLeftWidth: 3, padding: spacing.md, marginBottom: spacing.sm, flexDirection: 'row', alignItems: 'flex-start', gap: spacing.sm },
  insightIcon: { fontSize: font.lg },
  insightText: { fontSize: font.sm, flex: 1, lineHeight: 18, fontWeight: '600' },
  cta:         { backgroundColor: colors.gold, borderRadius: radius.lg, paddingVertical: 14, alignItems: 'center', marginTop: spacing.sm },
  ctaTxt:      { color: colors.bg, fontSize: font.base, fontWeight: '800' },
});
