// ─── ProfilMedecinScreen.js — Profil & Prédiction Rx ──────────────────────
// Sources: Nb09 (Rx prediction AUC=1.0), Nb12 (NLP CamemBERT), Nb04 (Gemini brief)
import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors, spacing, radius, font } from '../theme';
import {
  RingChart, SectionLabel, Card, Pill, FlagsRow,
  SentimentBar, ProductRow, AlertStrip, KpiTile,
} from '../components/medecin';

// ── Data ──────────────────────────────────────────────────────────────────────
const DOCTOR = {
  name: 'Dr. Amina Bensalem',
  specialty: 'Cardiologue',
  city: 'Casablanca – Anfa',
  tier: 'A',
  tierColor: colors.teal,
  rxScore: 87,
  rxProg: 0.87,
  potential: 'HIGH',
  lastVisit: 'il y a 8 jours',
};

const NLP_FLAGS = [
  { label: '💊 Intérêt Produit A',     color: colors.teal   },
  { label: '📉 Objection prix',         color: colors.orange },
  { label: '🔬 Demande étude clinique', color: colors.blue   },
  { label: '✅ Satisfait suivi',        color: colors.green  },
  { label: '⚡ Urgence ordonnance',     color: colors.red    },
  { label: '🤝 Relation stable',        color: colors.purple },
];

const GEMINI_PRODUCTS = [
  { name: 'Cardiomax 10mg',  score: '92%', tag: 'Nb04 Gemini · Fit optimal',      tagColor: colors.teal   },
  { name: 'Vasorel Plus',    score: '78%', tag: 'Nb09 Score Rx · Prescripteur actif', tagColor: colors.blue   },
  { name: 'Hypertensol 5mg', score: '61%', tag: 'Nb04 · Potentiel secondaire',     tagColor: colors.t3     },
];

const KPIS = [
  { label: 'Visites / an',  value: '14',    color: colors.teal   },
  { label: 'Rx moy / mois', value: '23',    color: colors.blue   },
  { label: 'NPS médecin',   value: '+42',   color: colors.green  },
  { label: 'Taux réponse',  value: '91%',   color: colors.purple },
];

export default function ProfilMedecinScreen({ navigation }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <SafeAreaView style={s.safe}>
      <ScrollView style={s.scroll} contentContainerStyle={s.content} showsVerticalScrollIndicator={false}>

        {/* ── Header ── */}
        <View style={s.header}>
          <View style={s.avatar}>
            <Text style={s.avatarTxt}>AB</Text>
          </View>
          <View style={{ flex: 1 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: spacing.sm }}>
              <Text style={s.doctorName}>{DOCTOR.name}</Text>
              <Pill label={`Tier ${DOCTOR.tier}`} color={DOCTOR.tierColor} />
            </View>
            <Text style={s.specialty}>{DOCTOR.specialty} · {DOCTOR.city}</Text>
            <Text style={s.lastVisit}>Dernière visite {DOCTOR.lastVisit}</Text>
          </View>
        </View>

        {/* ── Alert strip ── */}
        <AlertStrip text="Prochaine visite recommandée dans 5 jours · Agent Coaching" color={colors.blue} />

        {/* ── KPIs ── */}
        <View style={s.kpiRow}>
          {KPIS.map((k, i) => <KpiTile key={i} {...k} style={i < KPIS.length - 1 ? { marginRight: spacing.xs } : {}} />)}
        </View>

        {/* ── Rx Prediction ring (Nb09) ── */}
        <SectionLabel title="Prédiction Prescription" tag="Nb09 · AUC = 1.0" />
        <Card style={{ flexDirection: 'row', alignItems: 'center', gap: spacing.xl }}>
          <RingChart size={88} progress={DOCTOR.rxProg} color={DOCTOR.tierColor} label={`${DOCTOR.rxScore}%`} sublabel="Score Rx" />
          <View style={{ flex: 1 }}>
            <Text style={s.rxTitle}>Probabilité de prescription</Text>
            <Text style={s.rxSub}>Modèle Random Forest entraîné sur 18 mois d'historique ordonnances</Text>
            <View style={{ flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm }}>
              <Pill label="HIGH POTENTIAL" color={colors.teal} />
              <Pill label="Prescripteur Actif" color={colors.blue} />
            </View>
          </View>
        </Card>

        {/* ── Sentiment NLP (Nb12 CamemBERT) ── */}
        <SectionLabel title="Analyse Sentiment" tag="Nb12 · CamemBERT" />
        <Card>
          <SentimentBar positive={0.78} label="Analyse NLP dernière visite · Nb12" />
          <FlagsRow flags={NLP_FLAGS} />
        </Card>

        {/* ── Produits recommandés (Nb04 Gemini) ── */}
        <SectionLabel title="Produits recommandés" tag="Nb04 · Gemini AI" />
        <Card>
          {GEMINI_PRODUCTS.map((p, i) => (
            <ProductRow key={i} name={p.name} score={p.score} tag={p.tag} tagColor={p.tagColor} />
          ))}
        </Card>

        {/* ── Brief Gemini (Nb04) ── */}
        <SectionLabel title="Brief IA pré-visite" tag="Nb04 · Gemini Flash" />
        <Card>
          <Text style={s.briefText} numberOfLines={expanded ? undefined : 4}>
            Dr. Bensalem présente un profil Tier A avec un score Rx de 87%. Ses dernières interactions
            révèlent un intérêt marqué pour Cardiomax 10mg suite à une étude clinique partagée lors de la
            visite du 05/04. L'objection récurrente sur le prix suggère de préparer une argumentation
            pharmaco-économique. Priorité : renforcer la relation sur Vasorel Plus dont la prescription
            a augmenté de +34% ce trimestre. Éviter les créneaux 12h–14h (indisponible).
          </Text>
          <TouchableOpacity onPress={() => setExpanded(!expanded)} style={{ marginTop: spacing.sm }}>
            <Text style={{ color: colors.teal, fontSize: font.sm, fontWeight: '600' }}>
              {expanded ? 'Voir moins ▲' : 'Voir plus ▼'}
            </Text>
          </TouchableOpacity>
        </Card>

        {/* ── CTA ── */}
        <TouchableOpacity style={s.cta} onPress={() => navigation && navigation.navigate('HistoriqueVisites')}>
          <Text style={s.ctaTxt}>📋  Voir historique des visites</Text>
        </TouchableOpacity>

        <View style={{ height: spacing.xxl }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe:       { flex: 1, backgroundColor: colors.bg },
  scroll:     { flex: 1 },
  content:    { padding: spacing.lg },
  header:     { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.md, marginBottom: spacing.lg },
  avatar:     { width: 52, height: 52, borderRadius: 26, backgroundColor: colors.tealB, borderWidth: 2, borderColor: colors.teal, alignItems: 'center', justifyContent: 'center' },
  avatarTxt:  { color: colors.teal, fontSize: font.lg, fontWeight: '800' },
  doctorName: { color: colors.t1, fontSize: font.lg, fontWeight: '700' },
  specialty:  { color: colors.t2, fontSize: font.sm, marginTop: 2 },
  lastVisit:  { color: colors.t3, fontSize: font.xs, marginTop: 2 },
  kpiRow:     { flexDirection: 'row', marginBottom: spacing.sm },
  rxTitle:    { color: colors.t1, fontSize: font.base, fontWeight: '700' },
  rxSub:      { color: colors.t2, fontSize: font.sm, marginTop: 4, lineHeight: 18 },
  briefText:  { color: colors.t2, fontSize: font.sm, lineHeight: 20 },
  cta:        { backgroundColor: colors.teal, borderRadius: radius.lg, paddingVertical: 14, alignItems: 'center', marginTop: spacing.sm },
  ctaTxt:     { color: colors.bg, fontSize: font.base, fontWeight: '700' },
});
