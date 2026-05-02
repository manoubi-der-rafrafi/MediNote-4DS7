import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '@/constants/colors';
import { Typography } from '@/constants/typography';
import { Radius } from '@/constants/spacing';

interface EligCardProps {
  id: string;
  title: string;
  meta: string;
  isHighlight?: boolean;
}

export function EligCard({ id, title, meta, isHighlight = false }: EligCardProps) {
  return (
    <View style={[styles.container, isHighlight ? styles.highlight : styles.normal]}>
      <Text style={styles.id}>{id}</Text>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.meta}>{meta}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 12,
    borderRadius: Radius.md,
    borderWidth: 0.5,
    marginBottom: 8,
  },
  normal: {
    borderColor: Colors.border,
    backgroundColor: Colors.card,
  },
  highlight: {
    borderColor: Colors.pos,
    backgroundColor: 'rgba(74, 124, 89, 0.06)',
  },
  id: {
    fontSize: Typography.xxs,
    color: Colors.muted,
    fontWeight: Typography.semibold,
  },
  title: {
    fontSize: Typography.base,
    fontWeight: Typography.medium,
    color: Colors.text,
    marginTop: 4,
  },
  meta: {
    fontSize: Typography.xs,
    color: Colors.muted,
    marginTop: 2,
  },
});
