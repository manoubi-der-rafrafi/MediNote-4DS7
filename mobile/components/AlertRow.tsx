import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '@/constants/colors';
import { Typography } from '@/constants/typography';
import { Radius } from '@/constants/spacing';

interface AlertRowProps {
  type: 'error' | 'warn' | 'info';
  title: string;
  subtitle: string;
}

export function AlertRow({ type, title, subtitle }: AlertRowProps) {
  const typeColors = {
    error: { bg: 'rgba(185, 74, 72, 0.12)', color: Colors.neg },
    warn: { bg: 'rgba(184, 134, 11, 0.14)', color: Colors.warn },
    info: { bg: Colors.brandSoft, color: Colors.brand },
  };

  const styles = typeColors[type];

  return (
    <View style={containerStyles.container}>
      <View style={[containerStyles.iconBox, { backgroundColor: styles.bg }]}>
        <Text style={[containerStyles.icon, { color: styles.color }]}>
          {type === 'error' ? '✕' : type === 'warn' ? '⚠' : 'ℹ'}
        </Text>
      </View>
      <View style={containerStyles.body}>
        <Text style={containerStyles.title}>{title}</Text>
        <Text style={containerStyles.subtitle}>{subtitle}</Text>
      </View>
    </View>
  );
}

const containerStyles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 8,
  },
  iconBox: {
    width: 32,
    height: 32,
    borderRadius: Radius.sm,
    justifyContent: 'center',
    alignItems: 'center',
    flexShrink: 0,
  },
  icon: {
    fontSize: 14,
    fontWeight: Typography.semibold,
  },
  body: {
    flex: 1,
  },
  title: {
    fontSize: Typography.sm,
    fontWeight: Typography.medium,
    color: Colors.text,
  },
  subtitle: {
    fontSize: Typography.xs,
    color: Colors.muted,
    marginTop: 2,
  },
});
