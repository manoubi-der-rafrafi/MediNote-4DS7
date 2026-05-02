import { View, StyleSheet } from 'react-native';
import { KpiCard } from './KpiCard';

interface KpiData {
  label: string;
  value: string;
  delta?: string;
  deltaType?: 'up' | 'down' | 'neutral';
}

interface KpiGridProps {
  kpis: KpiData[];
}

export function KpiGrid({ kpis }: KpiGridProps) {
  return (
    <View style={styles.container}>
      {kpis.map((kpi, index) => (
        <KpiCard key={index} style={styles.card} {...kpi} />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 12,
  },
  card: {
    flex: 1,
    minWidth: '45%',
  },
});
