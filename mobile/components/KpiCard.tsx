import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '@/constants/colors';
import { Typography } from '@/constants/typography';
import { Radius } from '@/constants/spacing';

interface KpiCardProps {
  label: string;
  value: string;
  delta?: string;
  deltaType?: 'up' | 'down' | 'neutral';
  style?: object;
}

export function KpiCard({ label, value, delta, deltaType = 'neutral', style }: KpiCardProps) {
  const deltaColor = deltaType === 'up' ? Colors.pos : deltaType === 'down' ? Colors.neg : Colors.muted;

  return (
    <View style={[styles.container, style]}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value}>{value}</Text>
      {delta && <Text style={[styles.delta, { color: deltaColor }]}>{delta}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.card,
    borderWidth: 0.5,
    borderColor: Colors.border,
    borderRadius: Radius.lg,
    padding: 12,
  },
  label: {
    fontSize: Typography.xxs,
    color: Colors.muted,
    textTransform: 'uppercase',
  },
  value: {
    fontSize: 20,
    fontWeight: Typography.regular,
    color: Colors.text,
    marginTop: 6,
  },
  delta: {
    fontSize: 10.5,
    marginTop: 4,
  },
});
