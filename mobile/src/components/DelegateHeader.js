// ─── DelegateHeader.js — Session Delegate Info Display ──────────────────────
import React, { useContext } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { SessionContext } from '../context/SessionContext';
import { colors } from '../theme';

export default function DelegateHeader() {
  // Safe access to session context; avoid crash if provider is not present
  const session = useContext(SessionContext) || {};
  const currentDelegate = session.currentDelegate;

  if (!currentDelegate) return null;

  return (
    <View style={styles.container}>
      <View style={styles.info}>
        <View>
          <Text style={styles.name}>{currentDelegate.nom}</Text>
          <Text style={styles.region}>📍 {currentDelegate.region}</Text>
        </View>
        <View style={[styles.scoreBadge, { backgroundColor: currentDelegate.color + '20' }]}>
          <Text style={[styles.scoreValue, { color: currentDelegate.color }]}>
            {currentDelegate.score}
          </Text>
          <Text style={[styles.scoreTier, { color: currentDelegate.color }]}>
            {currentDelegate.tier}
          </Text>
        </View>
      </View>
      <View style={styles.meta}>
        <Text style={styles.metaText}>🆔 #{currentDelegate.id_deleg}</Text>
        <Text style={styles.metaText}>📧 {currentDelegate.email}</Text>
        <Text style={styles.metaText}>📱 {currentDelegate.phone}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.s2,
    borderBottomWidth: 1,
    borderBottomColor: colors.bd,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  info: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  name: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.t1,
    marginBottom: 2,
  },
  region: {
    fontSize: 11,
    color: colors.t2,
  },
  scoreBadge: {
    borderRadius: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    alignItems: 'center',
    minWidth: 60,
  },
  scoreValue: {
    fontSize: 16,
    fontWeight: '800',
  },
  scoreTier: {
    fontSize: 8,
    fontWeight: '600',
    marginTop: 2,
  },
  meta: {
    backgroundColor: colors.s1,
    borderRadius: 6,
    padding: 8,
    gap: 4,
  },
  metaText: {
    fontSize: 9,
    color: colors.t2,
    fontWeight: '500',
  },
});
