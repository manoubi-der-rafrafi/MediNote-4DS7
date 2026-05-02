// ─── AlertesStockScreen.js — Alertes Expiry + Segment ─────────────────────────
// Sources: Nb07 (expiry 4 levels), Nb03 (segmentation ADVOCATE/HIGH OPP/LOYAL/URGENT)
import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView,
  TouchableOpacity, SafeAreaView,
} from 'react-native';
import { colors, spacing, radius, font } from '../theme';
import {
  RingChart, SectionLabel, Card, Pill, KpiTile,
  ExpiryRow, SegmentBadge, ActionItem, ProgressBar,
} from '../components/pharmacie';
import { usePharmacyData } from '../hooks/usePharmacyData';

// ── Data ──────────────────────────────────────────────────────────────────────
const PHARMACY = {
  name: 'Pharmacie Al Amal',
  city: 'Rabat – Agdal',
  segment: 'ADVOCATE',
  segmentColor: colors.teal,
  tierColor: colors.teal,
  tier: 'A',
};

const KPIS = [
  { label: 'Alertes actives', value: '7',     color: colors.red    },
  { label: 'Impact financier', value: '−186k', color: colors.orange },
  { label: 'Segment',          value: 'ADVO', color: colors.teal   },
  { label: 'Score fidélité',   value: '89%',  color: colors.gold   },
];

const EXPIRY_ROWS = [
  { product: 'Cardiomax 10mg',  lot: 'LOT-2241', days: 12, impact: '−68k MAD', level: 'CRITICAL' },
  { product: 'Vasorel Plus',    lot: 'LOT-2189', days: 24, impact: '−47k MAD', level: 'CRITICAL' },
  { product: 'Hypertensol 5mg', lot: 'LOT-2310', days: 38, impact: '−29k MAD', level: 'URGENT'   },
  { product: 'Diuremax 40mg',   lot: 'LOT-2445', days: 52, impact: '−22k MAD', level: 'URGENT'   },
  { product: 'Cholestop Plus',  lot: 'LOT-2501', days: 68, impact: '−12k MAD', level: 'WATCH'    },
  { product: 'Betacor 25mg',    lot: 'LOT-2567', days: 85, impact: '−8k MAD',  level: 'WATCH'    },
  { product: 'Aspérine Cardio', lot: 'LOT-2604', days: 112, impact: '−4k MAD', level: 'OK'       },
];

const ACTIONS = [
  { icon: '🔄', title: 'Retour fournisseur Cardiomax · LOT-2241', sub: 'Contacter DAM avant le 18/04 · Agent Alerte', color: colors.red    },
  { icon: '💰', title: 'Offre compensation Vasorel Plus', sub: 'Remise 15% sur prochain lot · Nb07', color: colors.orange },
  { icon: '📦', title: 'Réappro urgente Hypertensol 5mg', sub: 'Stock critique + expiry · Agent Territoire', color: colors.gold   },
  { icon: '🎯', title: 'Animation ADVOCATE programmée', sub: 'Nb03 segment · Potentiel ROI +34%', color: colors.teal   },
];

const LEVEL_SUMMARY = [
  { level: 'CRITICAL', count: 2, pct: 66, color: colors.red    },
  { level: 'URGENT',   count: 2, pct: 51, color: colors.orange },
  { level: 'WATCH',    count: 2, pct: 35, color: colors.gold   },
  { level: 'OK',       count: 1, pct: 12, color: colors.green  },
];

export default function AlertesStockScreen({ navigation }) {
  const [filter, setFilter] = useState('Tous');
  const { operations, risk, loading: apiLoading } = usePharmacyData(123);

  const alertCount = risk?.alert_count ?? operations?.pending_orders ?? 7;
  const KPIS_LIVE = [
    { ...KPIS[0], value: String(alertCount) },
    ...KPIS.slice(1),
  ];

  const apiExpiry = Array.isArray(operations?.expiry_alerts) && operations.expiry_alerts.length > 0
    ? operations.expiry_alerts.map((e) => ({
        product: e.product_name || e.name || 'Product',
        lot: e.lot_number || e.lot || '—',
        days: e.days_until_expiry ?? e.days ?? 30,
        impact: e.financial_impact || e.impact || '—',
        level: e.level || (e.days_until_expiry < 14 ? 'CRITICAL' : e.days_until_expiry < 30 ? 'URGENT' : 'WATCH'),
      }))
    : null;
  const EXPIRY_DATA = apiExpiry || EXPIRY_ROWS;

  const filters = ['Tous', 'CRITICAL', 'URGENT', 'WATCH', 'OK'];
  const filtered = filter === 'Tous' ? EXPIRY_DATA : EXPIRY_DATA.filter(r => r.level === filter);

  return (
    <SafeAreaView style={s.safe}>
      <ScrollView style={s.scroll} contentContainerStyle={s.content} showsVerticalScrollIndicator={false}>

        {/* ── Header ── */}
        <View style={s.header}>
          <View style={s.avatar}>
            <Text style={s.avatarTxt}>💊</Text>
          </View>
          <View style={{ flex: 1 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: spacing.sm }}>
              <Text style={s.pharmName}>{PHARMACY.name}</Text>
              <SegmentBadge segment={PHARMACY.segment} />
            </View>
            <Text style={s.pharmCity}>{PHARMACY.city}</Text>
          </View>
        </View>

        {/* ── KPIs ── */}
        <View style={s.kpiRow}>
          {KPIS_LIVE.map((k, i) => <KpiTile key={i} {...k} style={i < KPIS_LIVE.length - 1 ? { marginRight: spacing.xs } : {}} />)}
        </View>

        {/* ── Impact ring (Nb07) ── */}
        <SectionLabel title="Impact financier expiry" tag="Nb07 · 4 niveaux de risque" />
        <Card style={{ flexDirection: 'row', alignItems: 'center', gap: spacing.xl }}>
          <RingChart size={88} progress={0.72} color={colors.red} label="−186k" sublabel="MAD" />
          <View style={{ flex: 1 }}>
            <Text style={s.impactTitle}>7 lots à risque identifiés</Text>
            <Text style={s.impactSub}>Modèle Nb07 — classification multi-seuil sur date d'expiration + valeur stock</Text>
            <View style={{ flexDirection: 'row', gap: spacing.xs, marginTop: spacing.sm, flexWrap: 'wrap' }}>
              {LEVEL_SUMMARY.map((l, i) => (
                <Pill key={i} label={`${l.count} ${l.level}`} color={l.color} />
              ))}
            </View>
          </View>
        </Card>

        {/* ── Level distribution bar ── */}
        <Card style={{ paddingBottom: spacing.sm }}>
          <Text style={{ color: colors.t2, fontSize: font.sm, fontWeight: '600', marginBottom: spacing.md }}>Répartition par niveau · Nb07</Text>
          {LEVEL_SUMMARY.map((l, i) => (
            <ProgressBar key={i} label={l.level} value={l.count} max={7} color={l.color} />
          ))}
        </Card>

        {/* ── Segment Nb03 ── */}
        <SectionLabel title="Segment Pharmacie" tag="Nb03 · K-Means clustering" />
        <Card style={{ flexDirection: 'row', alignItems: 'center', gap: spacing.lg }}>
          <RingChart size={72} progress={0.89} color={colors.teal} label="89%" sublabel="fidélité" />
          <View style={{ flex: 1 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginBottom: spacing.xs }}>
              <SegmentBadge segment="ADVOCATE" />
            </View>
            <Text style={s.segSub}>Top 12% des pharmacies · Nb03 clustering 4 segments sur 420 pharmacies</Text>
            <Text style={{ color: colors.teal, fontSize: font.sm, fontWeight: '700', marginTop: spacing.xs }}>Potentiel animation +34% ROI</Text>
          </View>
        </Card>

        {/* ── Filters ── */}
        <SectionLabel title="Lots en risque" tag={`${filtered.length} lots`} />
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: spacing.md }}>
          <View style={{ flexDirection: 'row', gap: spacing.sm }}>
            {filters.map(f => (
              <TouchableOpacity
                key={f}
                onPress={() => setFilter(f)}
                style={[s.filterBtn, filter === f && s.filterActive]}
              >
                <Text style={[s.filterTxt, filter === f && { color: colors.gold }]}>{f}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>

        <Card>
          {filtered.map((row, i) => (
            <ExpiryRow key={i} {...row} />
          ))}
        </Card>

        {/* ── Actions ── */}
        <SectionLabel title="Actions recommandées" tag="Agent Alerte Stratégique" />
        <Card>
          {ACTIONS.map((a, i) => <ActionItem key={i} {...a} />)}
        </Card>

        {/* ── CTA ── */}
        <TouchableOpacity style={s.cta} onPress={() => navigation && navigation.navigate('AnalysePharmacien')}>
          <Text style={s.ctaTxt}>📊  Analyse & Opportunités</Text>
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
  header:       { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.md, marginBottom: spacing.lg },
  avatar:       { width: 52, height: 52, borderRadius: 26, backgroundColor: colors.goldB, borderWidth: 2, borderColor: colors.gold, alignItems: 'center', justifyContent: 'center' },
  avatarTxt:    { fontSize: font.xxl },
  pharmName:    { color: colors.t1, fontSize: font.lg, fontWeight: '700' },
  pharmCity:    { color: colors.t3, fontSize: font.sm, marginTop: 2 },
  kpiRow:       { flexDirection: 'row', marginBottom: spacing.sm },
  impactTitle:  { color: colors.t1, fontSize: font.base, fontWeight: '700' },
  impactSub:    { color: colors.t2, fontSize: font.sm, marginTop: 4, lineHeight: 18 },
  segSub:       { color: colors.t2, fontSize: font.sm, lineHeight: 18 },
  filterBtn:    { paddingHorizontal: spacing.md, paddingVertical: spacing.xs, borderRadius: radius.full, backgroundColor: colors.s2, borderWidth: 1, borderColor: colors.bd },
  filterActive: { borderColor: colors.gold, backgroundColor: colors.goldB },
  filterTxt:    { color: colors.t2, fontSize: font.sm, fontWeight: '600' },
  cta:          { backgroundColor: colors.gold, borderRadius: radius.lg, paddingVertical: 14, alignItems: 'center', marginTop: spacing.sm },
  ctaTxt:       { color: colors.bg, fontSize: font.base, fontWeight: '800' },
});
