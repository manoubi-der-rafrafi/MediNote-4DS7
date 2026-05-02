import { View, Text, StyleSheet, StatusBar } from 'react-native';
import { Colors } from '@/constants/colors';
import { Typography } from '@/constants/typography';

interface TopBarProps {
  eyebrow: string;
  title: string;
  subtitle: string;
}

export function TopBar({ eyebrow, title, subtitle }: TopBarProps) {
  const statusBarHeight = StatusBar.currentHeight || 0;

  return (
    <View style={[styles.container, { paddingTop: 14 + statusBarHeight }]}>
      <Text style={styles.eyebrow}>{eyebrow}</Text>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.subtitle}>{subtitle}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.card,
    borderBottomWidth: 0.5,
    borderBottomColor: Colors.border,
    paddingHorizontal: 18,
    paddingBottom: 10,
  },
  eyebrow: {
    fontSize: Typography.xxs,
    color: Colors.brand,
    fontWeight: Typography.semibold,
    letterSpacing: 0.08,
    textTransform: 'uppercase',
  },
  title: {
    fontSize: Typography.xl,
    fontWeight: Typography.medium,
    color: Colors.text,
    marginTop: 2,
  },
  subtitle: {
    fontSize: Typography.sm,
    color: Colors.muted,
    marginTop: 2,
  },
});
