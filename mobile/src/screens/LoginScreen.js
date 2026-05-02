// ─── LoginScreen.js — Délégué CRM Pharma ─────────────────────────────────────
import React, { useState, useContext } from 'react';
import {
  View,
  TextInput,
  TouchableOpacity,
  Text,
  StyleSheet,
  Alert,
  ScrollView,
} from 'react-native';
import { colors } from '../theme';
import { SessionContext } from '../context/SessionContext';

export default function LoginScreen({ onLoginSuccess, onModeSelect }) {
  const { loginDelegate, delegates } = useContext(SessionContext);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const getUserMode = (user) => {
    const lower = user.toLowerCase().trim();
    if (lower.startsWith('med')) return 'medecin';
    if (lower.startsWith('ph')) return 'pharmacie';
    if (lower.startsWith('del')) return 'delegate';
    return null;
  };

  const handleLogin = () => {
    const user = username.trim();
    const pass = password.trim();
    const mode = getUserMode(user);

    if (!mode) {
      Alert.alert('Mode invalide', 'Utilisateur doit commencer par: med, ph, ou del');
      return;
    }
    if (!pass) {
      Alert.alert('Mot de passe requis', 'Entrez un mot de passe.');
      return;
    }

    if (mode === 'delegate') {
      const success = loginDelegate(541);
      if (success) {
        if (onModeSelect) onModeSelect('delegate');
        if (onLoginSuccess) onLoginSuccess();
      } else {
        Alert.alert('Erreur', 'Délégué non trouvé');
      }
    } else if (mode === 'medecin') {
      if (onModeSelect) onModeSelect('medecin');
      if (onLoginSuccess) onLoginSuccess();
    } else if (mode === 'pharmacie') {
      if (onModeSelect) onModeSelect('pharmacie');
      if (onLoginSuccess) onLoginSuccess();
    }
  };

  const handleQuickLogin = (id_deleg) => {
    const success = loginDelegate(id_deleg);
    if (success) {
      onModeSelect && onModeSelect('delegate');
      onLoginSuccess();
    }
  };

  const delegateList = Object.values(delegates);

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 60 }}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>CRM Pharma</Text>
        <Text style={styles.subtitle}>Médecin • Pharmacie • Délégué</Text>
      </View>

      {/* Standard Login Form */}
      <View style={styles.formSection}>
        <Text style={styles.sectionTitle}>Connexion Standard</Text>
        <View style={styles.form}>
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Nom d'utilisateur</Text>
            <TextInput
              style={styles.input}
              placeholder="Entrez votre identifiant"
              placeholderTextColor={colors.t3}
              value={username}
              onChangeText={setUsername}
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Mot de passe</Text>
            <TextInput
              style={styles.input}
              placeholder="Entrez votre mot de passe"
              placeholderTextColor={colors.t3}
              value={password}
              onChangeText={setPassword}
              secureTextEntry
            />
          </View>

          <TouchableOpacity
            style={styles.loginButton}
            onPress={handleLogin}
          >
            <Text style={styles.loginButtonText}>🔓 Se connecter</Text>
          </TouchableOpacity>

          <View style={styles.hint}>
            <Text style={styles.hintText}>💡 Exemples:</Text>
            <Text style={styles.hintText}>   👨‍⚕️ med* (Médecin)</Text>
            <Text style={styles.hintText}>   💊 ph* (Pharmacie)</Text>
            <Text style={styles.hintText}>   👛 del* (Délégué)</Text>
          </View>
        </View>
      </View>

      {/* Quick Delegate Selection */}
      <View style={styles.formSection}>
        <Text style={styles.sectionTitle}>Accès Rapide - Délégués</Text>
        <Text style={styles.sectionHint}>Cliquez sur un délégué pour accéder directement</Text>
        
        <View style={styles.delegateGrid}>
          {delegateList.map((delegate) => (
            <TouchableOpacity
              key={delegate.id_deleg}
              style={[
                styles.delegateCard,
                { borderLeftColor: delegate.color }
              ]}
              onPress={() => handleQuickLogin(delegate.id_deleg)}
            >
              <View style={styles.delegateHeader}>
                <Text style={styles.delegateId}>#{delegate.id_deleg}</Text>
                <Text style={[styles.delegateScore, { color: delegate.color }]}>
                  {delegate.score}
                </Text>
              </View>
              <Text style={styles.delegateName}>{delegate.nom}</Text>
              <Text style={styles.delegateRegion}>{delegate.region}</Text>
              <View style={styles.delegateFooter}>
                <Text style={styles.delegateTier}>{delegate.tier}</Text>
                <Text style={styles.delegateZone}>{delegate.zone}</Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Footer */}
      <View style={styles.footer}>
        <Text style={styles.footerText}>© 2026 Pharma Solutions</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
    paddingHorizontal: 16,
    paddingTop: 40,
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  title: {
    fontSize: 32,
    fontWeight: '700',
    color: colors.green,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: colors.t2,
    letterSpacing: 1,
  },
  formSection: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.t1,
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  sectionHint: {
    fontSize: 11,
    color: colors.t3,
    marginBottom: 12,
  },
  form: {
    width: '100%',
  },
  inputGroup: {
    marginBottom: 16,
  },
  label: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.t1,
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  input: {
    backgroundColor: colors.s1,
    borderWidth: 1,
    borderColor: colors.bd,
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 14,
    color: colors.t1,
  },
  loginButton: {
    backgroundColor: colors.green,
    borderRadius: 8,
    paddingVertical: 14,
    paddingHorizontal: 24,
    alignItems: 'center',
    marginTop: 20,
    shadowColor: colors.green,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  loginButtonDisabled: {
    opacity: 0.6,
  },
  loginButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.bg,
  },
  hint: {
    marginTop: 16,
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: colors.s1,
    borderRadius: 6,
    borderLeftWidth: 3,
    borderLeftColor: colors.blue,
  },
  hintText: {
    fontSize: 12,
    color: colors.t2,
  },
  delegateGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  delegateCard: {
    width: '48%',
    backgroundColor: colors.s2,
    borderRadius: 8,
    borderLeftWidth: 4,
    padding: 12,
    marginBottom: 12,
    borderTopWidth: 1,
    borderTopColor: colors.bd,
  },
  delegateHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  delegateId: {
    fontSize: 10,
    color: colors.t3,
    fontWeight: '600',
  },
  delegateScore: {
    fontSize: 18,
    fontWeight: '800',
  },
  delegateName: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.t1,
    marginBottom: 2,
  },
  delegateRegion: {
    fontSize: 10,
    color: colors.t2,
    marginBottom: 8,
  },
  delegateFooter: {
    borderTopWidth: 1,
    borderTopColor: colors.bd,
    paddingTop: 8,
  },
  delegateTier: {
    fontSize: 9,
    fontWeight: '600',
    color: colors.green,
    marginBottom: 2,
  },
  delegateZone: {
    fontSize: 9,
    color: colors.t3,
  },
  footer: {
    alignItems: 'center',
    marginTop: 20,
    paddingBottom: 20,
  },
  footerText: {
    fontSize: 11,
    color: colors.t3,
  },
});
