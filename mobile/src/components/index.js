// ─── Shared Components ────────────────────────────────────────────────────────
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Svg, { Circle } from 'react-native-svg';
import { colors, radius, spacing, typography } from '../theme';

// ── RingChart ────────────────────────────────────────────────────────────────
export function RingChart({ size = 76, progress = 0.82, color = colors.green, label }) {
  const strokeWidth = 7;
  const r = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * r;
  const offset = circumference * (1 - progress);

  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      <Svg width={size} height={size} style={{ position: 'absolute' }}>
        {/* bg track */}
        <Circle
          cx={size / 2} cy={size / 2} r={r}
          fill="none" stroke={colors.s3}
          strokeWidth={strokeWidth}
        />
        {/* progress arc */}
        <Circle
          cx={size / 2} cy={size / 2} r={r}
          fill="none" stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          rotation="-90"
          origin={`${size / 2}, ${size / 2}`}
        />
      </Svg>
      <Text style={{ fontSize: size > 60 ? 13 : 11, fontWeight: '900', color }}>
        {label}
      </Text>
    </View>
  );
}

// ── Pill / Badge ─────────────────────────────────────────────────────────────
const PILL_VARIANTS = {
  green:  { bg: colors.greenB,  border: colors.greenE,  text: colors.green  },
  blue:   { bg: colors.blueB,   border: colors.blueE,   text: colors.blue   },
  orange: { bg: colors.orangeB, border: colors.orangeE, text: colors.orange },
  red:    { bg: colors.redB,    border: colors.redE,    text: colors.red    },
  purple: { bg: colors.purpleB, border: colors.purpleE, text: colors.purple },
  gold:   { bg: colors.goldB,   border: colors.goldE,   text: colors.gold   },
  teal:   { bg: colors.tealB,   border: colors.tealE,   text: colors.teal   },
};

export function Pill({ label, variant = 'green', style }) {
  const v = PILL_VARIANTS[variant] || PILL_VARIANTS.green;
  return (
    <View style={[{
      backgroundColor: v.bg,
      borderColor: v.border,
      borderWidth: 1,
      borderRadius: radius.full,
      paddingHorizontal: 7,
      paddingVertical: 2,
    }, style]}>
      <Text style={{ fontSize: 9, fontWeight: '700', color: v.text }}>{label}</Text>
    </View>
  );
}

// ── Flag badge ────────────────────────────────────────────────────────────────
export function Flag({ label, variant = 'blue' }) {
  return <Pill label={label} variant={variant} style={{ marginRight: 3, marginBottom: 3 }} />;
}

// ── FlagsRow ─────────────────────────────────────────────────────────────────
export function FlagsRow({ flags }) {
  return (
    <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: 4 }}>
      {flags.map((f, i) => <Flag key={i} label={f.label} variant={f.variant} />)}
    </View>
  );
}

// ── SectionLabel ─────────────────────────────────────────────────────────────
export function SectionLabel({ children, style }) {
  return (
    <Text style={[{
      fontSize: 8, fontWeight: '700', textTransform: 'uppercase',
      letterSpacing: 0.7, color: colors.t3, marginBottom: 4,
    }, style]}>
      {children}
    </Text>
  );
}

// ── Card ─────────────────────────────────────────────────────────────────────
export function Card({ children, style, padding = true }) {
  return (
    <View style={[{
      backgroundColor: colors.s2,
      borderColor: colors.bd,
      borderWidth: 1,
      borderRadius: radius.md,
      overflow: 'hidden',
      ...(padding ? { padding: spacing.md } : {}),
    }, style]}>
      {children}
    </View>
  );
}

// ── KpiTile ──────────────────────────────────────────────────────────────────
export function KpiTile({ value, label, delta, deltaUp, color, style }) {
  return (
    <View style={[{
      flex: 1,
      backgroundColor: colors.s2,
      borderColor: colors.bd,
      borderWidth: 1,
      borderRadius: radius.sm,
      padding: spacing.sm,
    }, style]}>
      <Text style={{ fontSize: 20, fontWeight: '900', letterSpacing: -0.5, color }}>
        {value}
      </Text>
      <Text style={{ fontSize: 8, color: colors.t2, marginTop: 1, fontWeight: '500' }}>
        {label}
      </Text>
      {delta ? (
        <Text style={{ fontSize: 8, fontWeight: '600', marginTop: 2, color: deltaUp ? colors.green : colors.red }}>
          {delta}
        </Text>
      ) : null}
    </View>
  );
}

// ── DoctorRow ─────────────────────────────────────────────────────────────────
export function DoctorRow({ initials, name, sub, pillLabel, pillVariant, avatarBg, avatarColor, onPress }) {
  return (
    <TouchableOpacity onPress={onPress} style={{
      backgroundColor: colors.s2, borderColor: colors.bd,
      borderWidth: 1, borderRadius: radius.sm,
      padding: 9, flexDirection: 'row', alignItems: 'center', gap: 9,
    }}>
      <View style={{
        width: 30, height: 30, borderRadius: 15,
        backgroundColor: avatarBg, alignItems: 'center', justifyContent: 'center',
      }}>
        <Text style={{ fontSize: 8, fontWeight: '900', color: avatarColor }}>{initials}</Text>
      </View>
      <View style={{ flex: 1 }}>
        <Text style={{ fontSize: 11, fontWeight: '700', color: colors.t1 }}>{name}</Text>
        <Text style={{ fontSize: 8, color: colors.t2, marginTop: 1 }}>{sub}</Text>
      </View>
      <Pill label={pillLabel} variant={pillVariant} />
    </TouchableOpacity>
  );
}

// ── ProgressBar ───────────────────────────────────────────────────────────────
export function ProgressBar({ progress, color, width = '100%' }) {
  return (
    <View style={{ height: 3, backgroundColor: colors.s3, borderRadius: 99, overflow: 'hidden', width }}>
      <View style={{
        height: 3, width: `${progress * 100}%`,
        backgroundColor: color, borderRadius: 99,
      }} />
    </View>
  );
}

// ── ScoreRow ──────────────────────────────────────────────────────────────────
export function ScoreRow({ label, score, color }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 7, marginBottom: 5 }}>
      <Text style={{ fontSize: 9, color: colors.t2, flex: 1 }}>{label}</Text>
      <ProgressBar progress={score / 10} color={color} width={60} />
      <Text style={{ fontSize: 9, fontWeight: '800', color, width: 26, textAlign: 'right' }}>
        {score.toFixed(1)}
      </Text>
    </View>
  );
}

// ── ActionItem ────────────────────────────────────────────────────────────────
export function ActionItem({ num, text }) {
  return (
    <View style={{
      flexDirection: 'row', gap: 8, alignItems: 'flex-start',
      paddingVertical: 6,
      borderBottomWidth: 1, borderBottomColor: colors.bd,
    }}>
      <View style={{
        width: 17, height: 17, borderRadius: 99,
        backgroundColor: colors.purpleB, borderWidth: 1, borderColor: colors.purpleE,
        alignItems: 'center', justifyContent: 'center',
      }}>
        <Text style={{ fontSize: 8, fontWeight: '800', color: colors.purple }}>{num}</Text>
      </View>
      <Text style={{ fontSize: 9, color: colors.t2, flex: 1, lineHeight: 14 }}>{text}</Text>
    </View>
  );
}

// ── AlertStrip ────────────────────────────────────────────────────────────────
export function AlertStrip({ icon, title, desc, bg, border, titleColor }) {
  return (
    <View style={{
      backgroundColor: bg, borderColor: border,
      borderWidth: 1, borderRadius: radius.sm,
      padding: spacing.sm, flexDirection: 'row', alignItems: 'flex-start', gap: 7,
    }}>
      <Text style={{ fontSize: 14 }}>{icon}</Text>
      <View style={{ flex: 1 }}>
        <Text style={{ fontSize: 9, fontWeight: '700', color: titleColor }}>{title}</Text>
        <Text style={{ fontSize: 8, color: titleColor, opacity: 0.7, marginTop: 1, lineHeight: 12 }}>{desc}</Text>
      </View>
    </View>
  );
}
