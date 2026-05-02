import { Text, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Colors } from '@/constants/colors';
import { Typography } from '@/constants/typography';
import { Radius } from '@/constants/spacing';

interface HeroCardProps {
  label: string;
  bigValue: string;
  subtitle: string;
}

export function HeroCard({ label, bigValue, subtitle }: HeroCardProps) {
  return (
    <LinearGradient
      colors={[Colors.brand, Colors.brand2]}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={styles.container}
    >
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.bigValue}>{bigValue}</Text>
      <Text style={styles.subtitle}>{subtitle}</Text>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 18,
    borderRadius: Radius.lg,
    marginBottom: 12,
  },
  label: {
    fontSize: 10.5,
    color: 'rgba(255, 255, 255, 0.85)',
    letterSpacing: 0.08,
    textTransform: 'uppercase',
  },
  bigValue: {
    fontSize: Typography.xxl,
    fontWeight: '300',
    color: '#FFFFFF',
    marginTop: 4,
  },
  subtitle: {
    fontSize: Typography.sm,
    color: 'rgba(255, 255, 255, 0.88)',
    marginTop: 4,
  },
});
