import { Text, StyleSheet, View } from 'react-native';
import { Colors } from '@/constants/colors';
import { Radius } from '@/constants/spacing';

interface ChipProps {
  label: string;
  variant?: 'pos' | 'neg' | 'warn' | 'br' | 'default';
}

export function Chip({ label, variant = 'default' }: ChipProps) {
  const variantStyles = {
    pos: { backgroundColor: 'rgba(74, 124, 89, 0.12)', color: Colors.pos },
    neg: { backgroundColor: 'rgba(185, 74, 72, 0.12)', color: Colors.neg },
    warn: { backgroundColor: 'rgba(184, 134, 11, 0.14)', color: Colors.warn },
    br: { backgroundColor: Colors.brandSoft, color: Colors.brand },
    default: { backgroundColor: '#F4F3EE', color: Colors.muted },
  };

  const styles = variantStyles[variant];

  return (
    <View style={[chipStyles.container, { backgroundColor: styles.backgroundColor }]}>
      <Text style={[chipStyles.text, { color: styles.color }]}>{label}</Text>
    </View>
  );
}

const chipStyles = StyleSheet.create({
  container: {
    borderRadius: Radius.full,
    paddingVertical: 3,
    paddingHorizontal: 8,
  },
  text: {
    fontSize: 10.5,
    fontWeight: '500',
  },
});
