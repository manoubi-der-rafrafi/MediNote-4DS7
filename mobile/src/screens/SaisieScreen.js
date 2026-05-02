// ─── Screen 3: Saisie visite ──────────────────────────────────────────────────
// Notebooks: Nb05 (quota DS4), Nb12 (NLP voice note → 16 flags)
import React, { useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, SafeAreaView,
  TouchableOpacity, Alert,
} from 'react-native';
import { colors, spacing, radius } from '../theme';
import { SectionLabel } from '../components';

// ─── Steps config ─────────────────────────────────────────────────────────────
const STEPS = ['Check-in', 'Détailing', 'Échantillons', 'Clôture'];
const CURRENT_STEP = 2; // 0-indexed → "Échantillons"

// ─── Products (quota from Nb05 / DS4) ────────────────────────────────────────
const INITIAL_PRODUCTS = [
  { id: 1, name: 'Cardixol 5mg',  qty: 3, quotaMax: 5, inQuota: true  },
  { id: 2, name: 'Cardixol 10mg', qty: 5, quotaMax: 6, inQuota: true  },
  { id: 3, name: 'Vasoprel 20mg', qty: 4, quotaMax: 3, inQuota: false },
];

// ─── Component ────────────────────────────────────────────────────────────────
export default function SaisieScreen({ navigation }) {
  const [products, setProducts] = useState(INITIAL_PRODUCTS);
  const [recording, setRecording] = useState(false);

  const updateQty = (id, delta) => {
    setProducts(prev => prev.map(p => {
      if (p.id !== id) return p;
      const newQty = Math.max(0, p.qty + delta);
      return { ...p, qty: newQty, inQuota: newQty <= p.quotaMax };
    }));
  };

  const handleRecord = () => {
    setRecording(r => !r);
    if (!recording) {
      // In production: start expo-av recording, send to NLP pipeline (Nb12 CamemBERT)
      Alert.alert('NLP · Nb12', 'Enregistrement démarré. CamemBERT extraira automatiquement les 16 flags.');
    }
  };

  return (
    <SafeAreaView style={s.safe}>
      {/* Header */}
      <View style={s.header}>
        <Text style={s.title}>Saisie visite</Text>
        <Text style={s.sub}>Dr Rousseau · CHU Bordeaux</Text>
      </View>

      {/* Progress steps */}
      <View style={s.stepsWrap}>
        <View style={s.stepTrack}>
          {STEPS.map((_, i) => (
            <View
              key={i}
              style={[
                s.stepBar,
                i < CURRENT_STEP && s.stepDone,
                i === CURRENT_STEP && s.stepCurrent,
                i < STEPS.length - 1 && { marginRight: 3 },
              ]}
            />
          ))}
        </View>
        <View style={s.stepNames}>
          {STEPS.map((name, i) => (
            <Text
              key={i}
              style={[s.stepName, i === CURRENT_STEP && s.stepNameActive]}
            >
              {name}
            </Text>
          ))}
        </View>
      </View>

      <ScrollView contentContainerStyle={s.scroll} showsVerticalScrollIndicator={false}>

        {/* GPS validated */}
        <View style={s.geoCard}>
          <View style={s.geoPulse} />
          <Text style={s.geoText}>✓ Présence validée — Agent GEO · 14h33</Text>
        </View>

        {/* Products & quota — Nb05 / DS4 */}
        <SectionLabel style={s.gap}>Échantillons · Agent Quota Nb05 / DS4</SectionLabel>
        <View style={s.productsCard}>
          {products.map((p, i) => (
            <View
              key={p.id}
              style={[s.productRow, i === products.length - 1 && { borderBottomWidth: 0 }]}
            >
              <Text style={s.productName}>{p.name}</Text>
              <View style={s.qtyCtrl}>
                <TouchableOpacity onPress={() => updateQty(p.id, -1)} style={s.qtyBtn}>
                  <Text style={s.qtyBtnText}>−</Text>
                </TouchableOpacity>
                <Text style={s.qtyVal}>{p.qty}</Text>
                <TouchableOpacity onPress={() => updateQty(p.id, +1)} style={s.qtyBtn}>
                  <Text style={s.qtyBtnText}>+</Text>
                </TouchableOpacity>
              </View>
              <Text style={p.inQuota ? s.quotaOk : s.quotaWarn}>
                {p.inQuota ? '✓ quota' : '⚠ hors quota'}
              </Text>
            </View>
          ))}
        </View>

        {/* Voice note → NLP Nb12 */}
        <SectionLabel style={s.gap}>Note vocale · CamemBERT Nb12</SectionLabel>
        <TouchableOpacity
          onPress={handleRecord}
          style={[s.recordBtn, recording && s.recordBtnActive]}
          activeOpacity={0.8}
        >
          <View style={[s.recordIcon, recording && { backgroundColor: colors.redB, borderColor: colors.redE }]}>
            <Text style={{ fontSize: 11 }}>{recording ? '⏹' : '🎙'}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={[s.recordLabel, recording && { color: colors.red }]}>
              {recording ? 'Enregistrement en cours...' : 'Maintenir pour enregistrer'}
            </Text>
            <Text style={s.recordSub}>
              {recording ? '● REC · NLP en temps réel' : '16 flags extraits automatiquement'}
            </Text>
          </View>
        </TouchableOpacity>

        {/* Quota summary */}
        {products.some(p => !p.inQuota) && (
          <View style={s.quotaAlert}>
            <Text style={s.quotaAlertText}>
              ⚠️  {products.filter(p => !p.inQuota).map(p => p.name).join(', ')} — dépassement quota. Confirmation manager requise.
            </Text>
          </View>
        )}

        {/* Next step CTA */}
        <TouchableOpacity
          style={s.cta}
          onPress={() => navigation.navigate('Score')}
          activeOpacity={0.85}
        >
          <Text style={s.ctaText}>Étape suivante →</Text>
        </TouchableOpacity>

      </ScrollView>
    </SafeAreaView>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  safe:            { flex: 1, backgroundColor: colors.s1 },
  header:          { padding: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.bd },
  title:           { fontSize: 15, fontWeight: '800', color: colors.t1, letterSpacing: -0.3 },
  sub:             { fontSize: 9, color: colors.t2, marginTop: 2 },

  stepsWrap:       { padding: spacing.sm, paddingHorizontal: spacing.md, backgroundColor: colors.s2, borderBottomWidth: 1, borderBottomColor: colors.bd },
  stepTrack:       { flexDirection: 'row', marginBottom: 4 },
  stepBar:         { flex: 1, height: 3, borderRadius: 99, backgroundColor: colors.s3 },
  stepDone:        { backgroundColor: colors.blue },
  stepCurrent:     { backgroundColor: colors.blue, opacity: 0.6 },
  stepNames:       { flexDirection: 'row', justifyContent: 'space-between' },
  stepName:        { fontSize: 7, color: colors.t3, fontWeight: '500' },
  stepNameActive:  { color: colors.blue, fontWeight: '700' },

  scroll:          { padding: spacing.md, paddingBottom: 32 },

  geoCard:         { backgroundColor: colors.greenB, borderColor: colors.greenE, borderWidth: 1, borderRadius: radius.sm, padding: spacing.sm, flexDirection: 'row', alignItems: 'center', gap: 7 },
  geoPulse:        { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.green, shadowColor: colors.green, shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0.5, shadowRadius: 4 },
  geoText:         { fontSize: 9, color: colors.green, fontWeight: '600' },

  gap:             { marginTop: spacing.md, marginBottom: spacing.xs },

  productsCard:    { backgroundColor: colors.s2, borderColor: colors.bd, borderWidth: 1, borderRadius: radius.sm, overflow: 'hidden' },
  productRow:      { flexDirection: 'row', alignItems: 'center', padding: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.bd },
  productName:     { flex: 1, fontSize: 11, fontWeight: '600', color: colors.t1 },
  qtyCtrl:         { flexDirection: 'row', alignItems: 'center', gap: 7 },
  qtyBtn:          { width: 24, height: 24, borderRadius: 6, backgroundColor: colors.s3, borderWidth: 1, borderColor: colors.bd, alignItems: 'center', justifyContent: 'center' },
  qtyBtnText:      { fontSize: 14, fontWeight: '700', color: colors.t2, lineHeight: 18 },
  qtyVal:          { fontSize: 13, fontWeight: '800', color: colors.t1, minWidth: 18, textAlign: 'center' },
  quotaOk:         { fontSize: 8, color: colors.green, fontWeight: '700', marginLeft: 7 },
  quotaWarn:       { fontSize: 8, color: colors.red, fontWeight: '700', marginLeft: 7 },

  recordBtn:       { backgroundColor: colors.s3, borderColor: colors.bd, borderWidth: 1, borderRadius: radius.sm, padding: spacing.sm, flexDirection: 'row', alignItems: 'center', gap: 8 },
  recordBtnActive: { borderColor: colors.redE, backgroundColor: colors.redB },
  recordIcon:      { width: 26, height: 26, borderRadius: 13, backgroundColor: colors.s2, borderWidth: 1, borderColor: colors.bd, alignItems: 'center', justifyContent: 'center' },
  recordLabel:     { fontSize: 10, fontWeight: '600', color: colors.t1 },
  recordSub:       { fontSize: 8, color: colors.t3, marginTop: 1 },

  quotaAlert:      { marginTop: spacing.sm, backgroundColor: colors.redB, borderColor: colors.redE, borderWidth: 1, borderRadius: radius.sm, padding: spacing.sm },
  quotaAlertText:  { fontSize: 9, color: colors.red, lineHeight: 14 },

  cta:             { marginTop: spacing.md, backgroundColor: colors.blue, borderRadius: radius.sm, paddingVertical: 12, alignItems: 'center' },
  ctaText:         { fontSize: 13, fontWeight: '700', color: '#fff' },
});
