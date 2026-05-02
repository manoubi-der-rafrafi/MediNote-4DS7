import { View, StyleSheet } from 'react-native';
import { Colors } from '@/constants/colors';

interface ProgressBarProps {
  percent: number;
  variant?: 'default' | 'warn' | 'neg' | 'pos';
}

export function ProgressBar({ percent, variant = 'default' }: ProgressBarProps) {
  const variantColors = {
    default: Colors.brand,
    warn: Colors.warn,
    neg: Colors.neg,
    pos: Colors.pos,
  };

  const fillColor = variantColors[variant];

  return (
    <View style={styles.container}>
      <View style={[styles.fill, { width: `${Math.min(100, Math.max(0, percent))}%`, backgroundColor: fillColor }]} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    height: 6,
    backgroundColor: '#F0EEEA',
    borderRadius: 4,
    overflow: 'hidden',
    marginTop: 6,
  },
  fill: {
    height: '100%',
    borderRadius: 4,
  },
});
