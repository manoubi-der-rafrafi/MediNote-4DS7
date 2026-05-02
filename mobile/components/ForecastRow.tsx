import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '@/constants/colors';
import { Typography } from '@/constants/typography';

interface ForecastRowProps {
  name: string;
  meta: string;
  value: string;
  valueSub: string;
}

export function ForecastRow({ name, meta, value, valueSub }: ForecastRowProps) {
  return (
    <View style={styles.container}>
      <View>
        <Text style={styles.name}>{name}</Text>
        <Text style={styles.meta}>{meta}</Text>
      </View>
      <View style={styles.right}>
        <Text style={styles.value}>{value}</Text>
        <Text style={styles.valueSub}>{valueSub}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 0.5,
    borderBottomColor: Colors.border,
  },
  name: {
    fontSize: 12.5,
    fontWeight: Typography.medium,
    color: Colors.text,
  },
  meta: {
    fontSize: 10.5,
    color: Colors.muted,
    marginTop: 2,
  },
  right: {
    alignItems: 'flex-end',
  },
  value: {
    fontSize: Typography.base,
    fontWeight: Typography.medium,
    color: Colors.text,
    textAlign: 'right',
  },
  valueSub: {
    fontSize: 10.5,
    color: Colors.muted,
    marginTop: 2,
    textAlign: 'right',
  },
});
