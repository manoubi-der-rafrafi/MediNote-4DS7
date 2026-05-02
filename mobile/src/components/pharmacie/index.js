// ─── components/pharmacie/index.js — Pharmacie shared UI ───────────────────────
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Svg, { Circle, Line } from 'react-native-svg';
import { colors, spacing, radius, font } from '../../theme';

const strokeWidth = 8;

// ── RingChart ─────────────────────────────────────────────────────────────────
export function RingChart({ size = 80, progress = 0.7, color = colors.gold, label, sublabel }) {
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
export function Pill({ label, color = colors.gold }) {
  return (
    <View style={{ backgroundColor: color + '22', borderRadius: radius.full, paddingHorizontal: spacing.sm, paddingVertical: 3, alignSelf: 'flex-start' }}>
      <Text style={{ color, fontSize: font.xs, fontWeight: '700' }}>{label}</Text>
    </View>
  );
}

// ── KpiTile ───────────────────────────────────────────────────────────────────
export function KpiTile({ label, value, sub, color = colors.gold, style }) {
  return (
    <View style={[{ flex: 1, backgroundColor: colors.s2, borderRadius: radius.md, padding: spacing.md, alignItems: 'center', borderWidth: 1, borderColor: colors.bd }, style]}>
      <Text style={{ color, fontSize: font.xl, fontWeight: '800' }}>{value}</Text>
      <Text style={{ color: colors.t2, fontSize: font.xs, marginTop: 2, textAlign: 'center' }}>{label}</Text>
      {sub ? <Text style={{ color: colors.t3, fontSize: font.xs, marginTop: 1 }}>{sub}</Text> : null}
    </View>
  );
}

// ── ExpiryBadge ───────────────────────────────────────────────────────────────
const LEVEL_COLORS = {
  CRITICAL: colors.red,
  URGENT:   colors.orange,
  WATCH:    colors.gold,
  OK:       colors.green,
};
export function ExpiryBadge({ level }) {
  const c = LEVEL_COLORS[level] || colors.t2;
  return (
    <View style={{ backgroundColor: c + '22', borderRadius: radius.full, paddingHorizontal: spacing.sm, paddingVertical: 3 }}>
      <Text style={{ color: c, fontSize: font.xs, fontWeight: '800' }}>{level}</Text>
    </View>
  );
}

// ── ExpiryRow ─────────────────────────────────────────────────────────────────
export function ExpiryRow({ product, lot, days, impact, level }) {
  const c = LEVEL_COLORS[level] || colors.t2;
  return (
    <View style={{ paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.bd }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: spacing.xs }}>
        <Text style={{ color: colors.t1, fontSize: font.base, fontWeight: '600', flex: 1 }}>{product}</Text>
        <ExpiryBadge level={level} />
      </View>
      <View style={{ flexDirection: 'row' }}>
        <Text style={{ color: colors.t3, fontSize: font.sm, flex: 1 }}>Lot {lot} · expire dans {days}j</Text>
        <Text style={{ color: c, fontSize: font.sm, fontWeight: '700' }}>{impact}</Text>
      </View>
    </View>
  );
}

// ── SegmentBadge ──────────────────────────────────────────────────────────────
const SEG_COLORS = {
  ADVOCATE:   colors.teal,
  'HIGH OPP': colors.gold,
  LOYAL:      colors.green,
  URGENT:     colors.red,
  STANDARD:   colors.t2,
};
export function SegmentBadge({ segment }) {
  const c = SEG_COLORS[segment] || colors.t2;
  return (
    <View style={{ backgroundColor: c + '22', borderRadius: radius.full, paddingHorizontal: spacing.md, paddingVertical: spacing.xs, borderWidth: 1, borderColor: c + '50' }}>
      <Text style={{ color: c, fontSize: font.sm, fontWeight: '800' }}>{segment}</Text>
    </View>
  );
}

// ── ProgressBar ───────────────────────────────────────────────────────────────
export function ProgressBar({ label, value, max, color = colors.gold, unit = '' }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <View style={{ marginBottom: spacing.md }}>
      <View style={{ flexDirection: 'row', marginBottom: spacing.xs }}>
        <Text style={{ color: colors.t2, fontSize: font.sm, flex: 1 }}>{label}</Text>
        <Text style={{ color, fontSize: font.sm, fontWeight: '700' }}>{value}{unit} / {max}{unit}</Text>
      </View>
      <View style={{ height: 6, borderRadius: radius.full, backgroundColor: colors.s3, overflow: 'hidden' }}>
        <View style={{ width: `${pct}%`, height: '100%', backgroundColor: color, borderRadius: radius.full }} />
      </View>
    </View>
  );
}

// ── MiniSparkline ─────────────────────────────────────────────────────────────
export function MiniSparkline({ data = [30, 45, 38, 55, 62, 58, 72], color = colors.gold, width = 80, height = 28 }) {
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
        <Line key={i} x1={p.x} y1={p.y} x2={points[i + 1].x} y2={points[i + 1].y} stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      ))}
    </Svg>
  );
}

// ── ActionItem ────────────────────────────────────────────────────────────────
export function ActionItem({ icon, title, sub, color = colors.gold }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'flex-start', paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.bd, gap: spacing.md }}>
      <View style={{ width: 32, height: 32, borderRadius: radius.full, backgroundColor: color + '22', alignItems: 'center', justifyContent: 'center' }}>
        <Text style={{ fontSize: font.base }}>{icon}</Text>
      </View>
      <View style={{ flex: 1 }}>
        <Text style={{ color: colors.t1, fontSize: font.sm, fontWeight: '600' }}>{title}</Text>
        {sub ? <Text style={{ color: colors.t3, fontSize: font.xs, marginTop: 2 }}>{sub}</Text> : null}
      </View>
    </View>
  );
}
