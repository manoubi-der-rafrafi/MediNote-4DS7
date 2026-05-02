import { View, Text, StyleSheet, ReactNode } from 'react-native';
import { Colors } from '@/constants/colors';
import { Typography } from '@/constants/typography';
import { Radius } from '@/constants/spacing';

interface ListRowProps {
  initials: string;
  title: string;
  subtitle?: string;
  rightElement?: ReactNode;
  bottomElement?: ReactNode;
}

export function ListRow({ initials, title, subtitle, rightElement, bottomElement }: ListRowProps) {
  return (
    <View style={styles.container}>
      <View style={styles.iconBox}>
        <Text style={styles.initials}>{initials}</Text>
      </View>
      <View style={styles.body}>
        <Text style={styles.title} numberOfLines={1}>{title}</Text>
        {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
        {bottomElement}
      </View>
      {rightElement && <View style={styles.right}>{rightElement}</View>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: Colors.card,
    borderWidth: 0.5,
    borderColor: Colors.border,
    borderRadius: Radius.md,
    marginBottom: 8,
  },
  iconBox: {
    width: 32,
    height: 32,
    borderRadius: Radius.sm,
    backgroundColor: Colors.brandSoft,
    justifyContent: 'center',
    alignItems: 'center',
    flexShrink: 0,
  },
  initials: {
    fontSize: 11,
    fontWeight: Typography.semibold,
    color: Colors.brand,
  },
  body: {
    flex: 1,
  },
  title: {
    fontSize: 12.5,
    fontWeight: Typography.medium,
    color: Colors.text,
  },
  subtitle: {
    fontSize: 10.5,
    color: Colors.muted,
    marginTop: 2,
  },
  right: {
    flexShrink: 0,
  },
});
