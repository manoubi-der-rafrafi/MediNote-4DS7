// ─── components/medecin/index.js — Médecin shared UI ──────────────────────────
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import Svg, { Circle, Line } from 'react-native-svg';
import { colors, spacing, radius, font } from '../../theme';

const strokeWidth = 8;

// ── RingChart ──────────────────────────────────────────────────────────────────
export function RingChart({ size = 80, progress = 0.85, color = colors.teal, label, sublabel }) {
  const r = (size - strokeWidth) / 2;
  const cx = size / 2;
  const cy = size / 2;
  const circumference = 2 * Math.PI * r;
  const offset = circumference * (1 - Math.min(Math.max(progress, 0), 1));
  return (
    <View style={{ alignItems: 'center' }}>
      <Svg width={size} height={size}>
        <Circle cx={cx} cy={cy} r={r} stroke={colors.s3} strokeWidth={strokeWidth} fill="none" />
        <Circle
          cx={cx} cy={cy} r={r}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={`${circumference} ${circumference}`}
          strokeDashoffset={offset}
          strokeLinecap="round"
          rotation="-90"
          origin={`${cx}, ${cy}`}
        />
      </Svg>
      {label ? (
        <View style={{ position: 'absolute', top: 0, left: 0, width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
          <Text style={{ color, fontSize: font.lg, fontWeight: '700' }}>{label}</Text>
          {sublabel ? <Text style={{ color: colors.t3, fontSize: font.xs, marginTop: 1 }}>{sublabel}</Text> : null}
        </View>
      ) : null}
    </View>
  );
}

// ── SectionLabel ──────────────────────────────────────────────────────────────
export function SectionLabel({ title, tag }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: spacing.sm, marginTop: spacing.lg }}>
      <Text style={{ color: colors.t2, fontSize: font.xs, fontWeight: '700', letterSpacing: 0.8, textTransform: 'uppercase', flex: 1 }}>{title}</Text>
      {tag ? <Text style={{ color: colors.t3, fontSize: font.xs }}>{tag}</Text> : null}
    </View>
  );
}

// ── Card ──────────────────────────────────────────────────────────────────────
export function Card({ children, style }) {
  return (
    <View style={[{ backgroundColor: colors.s1, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.bd, padding: spacing.lg, marginBottom: spacing.md }, style]}>
      {children}
    </View>
  );
}

// ── Pill ──────────────────────────────────────────────────────────────────────
export function Pill({ label, color = colors.teal, bg }) {
  return (
    <View style={{ backgroundColor: bg || (color + '22'), borderRadius: radius.full, paddingHorizontal: spacing.sm, paddingVertical: 3, alignSelf: 'flex-start' }}>
      <Text style={{ color, fontSize: font.xs, fontWeight: '700' }}>{label}</Text>
    </View>
  );
}

// ── Flag ──────────────────────────────────────────────────────────────────────
export function Flag({ label, color }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: colors.s2, borderRadius: radius.sm, paddingHorizontal: spacing.sm, paddingVertical: spacing.xs, marginRight: spacing.xs, marginBottom: spacing.xs, borderLeftWidth: 2, borderLeftColor: color }}>
      <Text style={{ color: colors.t1, fontSize: font.xs }}>{label}</Text>
    </View>
  );
}

// ── FlagsRow ──────────────────────────────────────────────────────────────────
export function FlagsRow({ flags }) {
  return (
    <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: spacing.sm }}>
      {flags.map((f, i) => <Flag key={i} label={f.label} color={f.color} />)}
    </View>
  );
}

// ── KpiTile ───────────────────────────────────────────────────────────────────
export function KpiTile({ label, value, sub, color = colors.teal, style }) {
  return (
    <View style={[{ flex: 1, backgroundColor: colors.s2, borderRadius: radius.md, padding: spacing.md, alignItems: 'center', borderWidth: 1, borderColor: colors.bd }, style]}>
      <Text style={{ color, fontSize: font.xl, fontWeight: '800' }}>{value}</Text>
      <Text style={{ color: colors.t2, fontSize: font.xs, marginTop: 2, textAlign: 'center' }}>{label}</Text>
      {sub ? <Text style={{ color: colors.t3, fontSize: font.xs, marginTop: 1 }}>{sub}</Text> : null}
    </View>
  );
}

// ── SentimentBar ──────────────────────────────────────────────────────────────
export function SentimentBar({ positive = 0.78, label = 'CamemBERT · Nb12' }) {
  const neg = 1 - positive;
  return (
    <View>
      <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: spacing.xs }}>
        <Text style={{ color: colors.t2, fontSize: font.sm, flex: 1 }}>{label}</Text>
        <Text style={{ color: colors.green, fontSize: font.sm, fontWeight: '700' }}>{Math.round(positive * 100)}% positif</Text>
      </View>
      <View style={{ height: 8, borderRadius: radius.full, backgroundColor: colors.s3, flexDirection: 'row', overflow: 'hidden' }}>
        <View style={{ width: `${positive * 100}%`, backgroundColor: colors.green }} />
        <View style={{ width: `${neg * 100}%`, backgroundColor: colors.red }} />
      </View>
    </View>
  );
}

// ── ProductRow ────────────────────────────────────────────────────────────────
export function ProductRow({ name, score, tag, tagColor }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.bd }}>
      <View style={{ flex: 1 }}>
        <Text style={{ color: colors.t1, fontSize: font.base, fontWeight: '600' }}>{name}</Text>
        {tag ? <Text style={{ color: tagColor || colors.t3, fontSize: font.xs, marginTop: 2 }}>{tag}</Text> : null}
      </View>
      <Text style={{ color: colors.teal, fontSize: font.base, fontWeight: '700' }}>{score}</Text>
    </View>
  );
}

// ── VisitRow ──────────────────────────────────────────────────────────────────
export function VisitRow({ date, tier, quality, score, color }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.bd }}>
      <Text style={{ color: colors.t3, fontSize: font.sm, width: 68 }}>{date}</Text>
      <View style={{ flex: 1 }}>
        <Text style={{ color: colors.t1, fontSize: font.sm, fontWeight: '600' }}>{quality}</Text>
      </View>
      <Pill label={`Tier ${tier}`} color={color} />
      <Text style={{ color, fontSize: font.sm, fontWeight: '700', marginLeft: spacing.sm, width: 32, textAlign: 'right' }}>{score}</Text>
    </View>
  );
}

// ── AlertStrip ────────────────────────────────────────────────────────────────
export function AlertStrip({ text, color = colors.orange }) {
  return (
    <View style={{ backgroundColor: color + '18', borderRadius: radius.md, borderWidth: 1, borderColor: color + '40', padding: spacing.md, marginBottom: spacing.md, flexDirection: 'row', alignItems: 'center' }}>
      <Text style={{ fontSize: font.base, marginRight: spacing.sm }}>⚠️</Text>
      <Text style={{ color, fontSize: font.sm, flex: 1, fontWeight: '600' }}>{text}</Text>
    </View>
  );
}

// ── MiniSparkline ─────────────────────────────────────────────────────────────
export function MiniSparkline({ data = [30, 45, 38, 55, 62, 58, 72], color = colors.teal, width = 80, height = 28 }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const step = width / (data.length - 1);
  const points = data.map((v, i) => ({
    x: i * step,
    y: height - ((v - min) / range) * height,
  }));
  return (
    <Svg width={width} height={height}>
      {points.slice(0, -1).map((p, i) => (
        <Line
          key={i}
          x1={p.x} y1={p.y}
          x2={points[i + 1].x} y2={points[i + 1].y}
          stroke={color}
          strokeWidth="1.5"
          strokeLinecap="round"
        />
      ))}
    </Svg>
  );
}
