// ─── screens/SettingsPharmacieScreen.js — Pharmacy Profile & Settings ──────
import React, { useState, useContext } from 'react';
import {
  View, Text, StyleSheet, ScrollView,
  TouchableOpacity, SafeAreaView, TextInput,
  Switch, Alert
} from 'react-native';
import { colors, spacing, radius, font } from '../theme';
import { ProfileContext } from '../context/ProfileContext';
import { SectionLabel, Card, Pill } from '../components/pharmacie';

export default function SettingsPharmacieScreen({ navigation, onLogout }) {
  const { profile, updateProfile, changePassword, notifications, updateNotificationSettings, security, enableTwoFactor } = useContext(ProfileContext);
  const [editMode, setEditMode] = useState(false);
  const [editedName, setEditedName] = useState(profile.name);
  const [editedEmail, setEditedEmail] = useState(profile.email);
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPasswordForm, setShowPasswordForm] = useState(false);

  const handleSaveProfile = () => {
    if (editedName.trim() && editedEmail.trim()) {
      updateProfile({ name: editedName, email: editedEmail });
      setEditMode(false);
      Alert.alert('✅ Succès', 'Profil mis à jour');
    }
  };

  const handleChangePassword = () => {
    if (!oldPassword || !newPassword || !confirmPassword) {
      Alert.alert('❌ Erreur', 'Remplissez tous les champs');
      return;
    }
    if (newPassword !== confirmPassword) {
      Alert.alert('❌ Erreur', 'Les mots de passe ne correspondent pas');
      return;
    }
    if (changePassword(oldPassword, newPassword)) {
      Alert.alert('✅ Succès', 'Mot de passe changé');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setShowPasswordForm(false);
    }
  };

  const handleLogout = () => {
    Alert.alert('Déconnexion', 'Êtes-vous sûr ?', [
      { text: 'Annuler', style: 'cancel' },
      { 
        text: 'Déconnecter', 
        style: 'destructive',
        onPress: () => onLogout && onLogout()
      }
    ]);
  };

  const handleChangeAvatar = () => {
    const avatars = ['💊', '🏥', '👨‍⚕️', '👩‍⚕️', '💉'];
    const randomAvatar = avatars[Math.floor(Math.random() * avatars.length)];
    updateProfile({ avatar: randomAvatar });
    Alert.alert('✅ Avatar changé', randomAvatar);
  };

  return (
    <SafeAreaView style={s.safe}>
      <ScrollView style={s.scroll} contentContainerStyle={s.content} showsVerticalScrollIndicator={false}>

        {/* Header */}
        <View style={s.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={s.backBtn}>
            <Text style={s.backTxt}>← Retour</Text>
          </TouchableOpacity>
          <Text style={s.pageTitle}>Paramètres du Profil</Text>
        </View>

        {/* Profile Card */}
        <SectionLabel title="Profil Pharmacie" />
        <Card>
          <View style={s.profileHeader}>
            <TouchableOpacity onPress={handleChangeAvatar}>
              <View style={s.avatarLarge}>
                <Text style={s.avatarText}>{profile.avatar}</Text>
              </View>
              <Text style={s.changeAvatarText}>Changer</Text>
            </TouchableOpacity>
            <View style={{ flex: 1, marginLeft: spacing.lg }}>
              <Text style={s.profileName}>{profile.name}</Text>
              <Text style={s.profileSubtitle}>{profile.email}</Text>
              <Text style={s.profileSubtitle}>{profile.company}</Text>
            </View>
          </View>

          <View style={s.profileStats}>
            <View style={s.stat}>
              <Text style={s.statValue}>{profile.region}</Text>
              <Text style={s.statLabel}>Région</Text>
            </View>
            <View style={s.stat}>
              <Text style={s.statValue}>{profile.joinDate}</Text>
              <Text style={s.statLabel}>Membre depuis</Text>
            </View>
          </View>
        </Card>

        {/* Edit Profile */}
        <SectionLabel title="Informations Personnelles" />
        {editMode ? (
          <Card>
            <View style={s.editForm}>
              <View style={s.inputGroup}>
                <Text style={s.label}>Nom de la pharmacie</Text>
                <TextInput
                  style={s.textInput}
                  value={editedName}
                  onChangeText={setEditedName}
                  placeholderTextColor={colors.t3}
                />
              </View>
              <View style={s.inputGroup}>
                <Text style={s.label}>Email</Text>
                <TextInput
                  style={s.textInput}
                  value={editedEmail}
                  onChangeText={setEditedEmail}
                  keyboardType="email-address"
                  placeholderTextColor={colors.t3}
                />
              </View>
              <View style={s.buttonGroup}>
                <TouchableOpacity style={[s.button, s.saveButton]} onPress={handleSaveProfile}>
                  <Text style={s.buttonText}>✅ Enregistrer</Text>
                </TouchableOpacity>
                <TouchableOpacity style={[s.button, s.cancelButton]} onPress={() => setEditMode(false)}>
                  <Text style={[s.buttonText, { color: colors.t2 }]}>✕ Annuler</Text>
                </TouchableOpacity>
              </View>
            </View>
          </Card>
        ) : (
          <Card>
            <View style={s.infoRow}>
              <View style={{ flex: 1 }}>
                <Text style={s.infoLabel}>Pharmacie</Text>
                <Text style={s.infoValue}>{profile.name}</Text>
              </View>
              <TouchableOpacity onPress={() => setEditMode(true)} style={s.editIcon}>
                <Text style={{ fontSize: font.lg }}>✏️</Text>
              </TouchableOpacity>
            </View>
            <View style={[s.infoRow, { marginTop: spacing.md }]}>
              <View style={{ flex: 1 }}>
                <Text style={s.infoLabel}>Email</Text>
                <Text style={s.infoValue}>{profile.email}</Text>
              </View>
            </View>
            <View style={[s.infoRow, { marginTop: spacing.md }]}>
              <View style={{ flex: 1 }}>
                <Text style={s.infoLabel}>Téléphone</Text>
                <Text style={s.infoValue}>{profile.phone}</Text>
              </View>
            </View>
          </Card>
        )}

        {/* Security */}
        <SectionLabel title="Sécurité" />
        {showPasswordForm ? (
          <Card>
            <View style={s.editForm}>
              <View style={s.inputGroup}>
                <Text style={s.label}>Ancien mot de passe</Text>
                <TextInput
                  style={s.textInput}
                  secureTextEntry
                  value={oldPassword}
                  onChangeText={setOldPassword}
                  placeholderTextColor={colors.t3}
                />
              </View>
              <View style={s.inputGroup}>
                <Text style={s.label}>Nouveau mot de passe</Text>
                <TextInput
                  style={s.textInput}
                  secureTextEntry
                  value={newPassword}
                  onChangeText={setNewPassword}
                  placeholderTextColor={colors.t3}
                />
              </View>
              <View style={s.inputGroup}>
                <Text style={s.label}>Confirmer le mot de passe</Text>
                <TextInput
                  style={s.textInput}
                  secureTextEntry
                  value={confirmPassword}
                  onChangeText={setConfirmPassword}
                  placeholderTextColor={colors.t3}
                />
              </View>
              <View style={s.buttonGroup}>
                <TouchableOpacity style={[s.button, s.saveButton]} onPress={handleChangePassword}>
                  <Text style={s.buttonText}>✅ Changer</Text>
                </TouchableOpacity>
                <TouchableOpacity style={[s.button, s.cancelButton]} onPress={() => setShowPasswordForm(false)}>
                  <Text style={[s.buttonText, { color: colors.t2 }]}>✕ Annuler</Text>
                </TouchableOpacity>
              </View>
            </View>
          </Card>
        ) : (
          <Card>
            <TouchableOpacity style={s.settingRow} onPress={() => setShowPasswordForm(true)}>
              <View>
                <Text style={s.settingTitle}>Changer le mot de passe</Text>
                <Text style={s.settingSubtitle}>Dernier changement: {security.lastPasswordChange}</Text>
              </View>
              <Text style={s.settingIcon}>🔐</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[s.settingRow, { marginTop: spacing.md }]}>
              <View>
                <Text style={s.settingTitle}>Authentification à deux facteurs</Text>
                <Text style={s.settingSubtitle}>{security.twoFactorEnabled ? 'Activée' : 'Désactivée'}</Text>
              </View>
              <Switch
                value={security.twoFactorEnabled}
                onValueChange={(val) => enableTwoFactor(val)}
                trackColor={{ false: colors.s3, true: colors.gold }}
                thumbColor={security.twoFactorEnabled ? colors.gold : colors.t2}
              />
            </TouchableOpacity>
          </Card>
        )}

        {/* Notifications */}
        <SectionLabel title="Notifications" />
        <Card>
          <TouchableOpacity style={s.settingRow}>
            <View>
              <Text style={s.settingTitle}>Alertes Email</Text>
              <Text style={s.settingSubtitle}>Recevoir les alertes de stock</Text>
            </View>
            <Switch
              value={notifications.emailAlerts}
              onValueChange={(val) => updateNotificationSettings({ emailAlerts: val })}
              trackColor={{ false: colors.s3, true: colors.gold }}
              thumbColor={notifications.emailAlerts ? colors.gold : colors.t2}
            />
          </TouchableOpacity>
          <TouchableOpacity style={[s.settingRow, { marginTop: spacing.md }]}>
            <View>
              <Text style={s.settingTitle}>Notifications Push</Text>
              <Text style={s.settingSubtitle}>Alertes expiry critiques</Text>
            </View>
            <Switch
              value={notifications.pushNotifications}
              onValueChange={(val) => updateNotificationSettings({ pushNotifications: val })}
              trackColor={{ false: colors.s3, true: colors.gold }}
              thumbColor={notifications.pushNotifications ? colors.gold : colors.t2}
            />
          </TouchableOpacity>
          <TouchableOpacity style={[s.settingRow, { marginTop: spacing.md }]}>
            <View>
              <Text style={s.settingTitle}>Rapport Hebdomadaire</Text>
              <Text style={s.settingSubtitle}>Performance & analytics</Text>
            </View>
            <Switch
              value={notifications.weeklyReport}
              onValueChange={(val) => updateNotificationSettings({ weeklyReport: val })}
              trackColor={{ false: colors.s3, true: colors.gold }}
              thumbColor={notifications.weeklyReport ? colors.gold : colors.t2}
            />
          </TouchableOpacity>
        </Card>

        {/* Logout */}
        <SectionLabel title="Compte" />
        <Card>
          <TouchableOpacity style={[s.logoutButton, s.logoutButtonWarning]} onPress={handleLogout}>
            <Text style={s.logoutButtonText}>🚪 Déconnexion</Text>
          </TouchableOpacity>
        </Card>

        <View style={{ height: spacing.xxl }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe:           { flex: 1, backgroundColor: colors.bg },
  scroll:         { flex: 1 },
  content:        { padding: spacing.lg },
  header:         { marginBottom: spacing.lg },
  backBtn:        { marginBottom: spacing.sm },
  backTxt:        { color: colors.gold, fontSize: font.sm, fontWeight: '600' },
  pageTitle:      { color: colors.t1, fontSize: font.xl, fontWeight: '800' },
  profileHeader:  { flexDirection: 'row', alignItems: 'flex-start', marginBottom: spacing.lg },
  avatarLarge:    { width: 64, height: 64, borderRadius: 32, backgroundColor: colors.goldB, borderWidth: 2, borderColor: colors.gold, alignItems: 'center', justifyContent: 'center' },
  avatarText:     { fontSize: font.xxl },
  changeAvatarText: { color: colors.gold, fontSize: font.xs, marginTop: 4, fontWeight: '600', textAlign: 'center' },
  profileName:    { color: colors.t1, fontSize: font.lg, fontWeight: '700' },
  profileSubtitle: { color: colors.t2, fontSize: font.sm, marginTop: 2 },
  profileStats:   { flexDirection: 'row', marginTop: spacing.lg, gap: spacing.md },
  stat:           { flex: 1, alignItems: 'center', paddingVertical: spacing.sm, borderTopWidth: 1, borderTopColor: colors.bd },
  statValue:      { color: colors.gold, fontSize: font.base, fontWeight: '700' },
  statLabel:      { color: colors.t3, fontSize: font.xs, marginTop: 2 },
  editForm:       { gap: spacing.md },
  inputGroup:     { marginBottom: spacing.sm },
  label:          { color: colors.t2, fontSize: font.sm, fontWeight: '600', marginBottom: spacing.xs },
  textInput:      { backgroundColor: colors.s2, borderRadius: radius.md, borderWidth: 1, borderColor: colors.bd, paddingHorizontal: spacing.md, paddingVertical: spacing.sm, color: colors.t1, fontSize: font.sm },
  buttonGroup:    { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.md },
  button:         { flex: 1, paddingVertical: spacing.md, borderRadius: radius.md, alignItems: 'center' },
  saveButton:     { backgroundColor: colors.gold },
  cancelButton:   { borderWidth: 1, borderColor: colors.bd, backgroundColor: colors.s2 },
  buttonText:     { color: colors.bg, fontSize: font.sm, fontWeight: '700' },
  infoRow:        { paddingVertical: spacing.sm, flexDirection: 'row', alignItems: 'center' },
  infoLabel:      { color: colors.t3, fontSize: font.xs, fontWeight: '600', marginBottom: 4 },
  infoValue:      { color: colors.t1, fontSize: font.base, fontWeight: '600' },
  editIcon:       { paddingVertical: spacing.sm, paddingLeft: spacing.md },
  settingRow:     { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.bd },
  settingTitle:   { color: colors.t1, fontSize: font.base, fontWeight: '600' },
  settingSubtitle: { color: colors.t3, fontSize: font.xs, marginTop: 2 },
  settingIcon:    { fontSize: font.lg },
  logoutButton:   { backgroundColor: colors.red, borderRadius: radius.lg, paddingVertical: spacing.lg, alignItems: 'center' },
  logoutButtonWarning: { backgroundColor: colors.red },
  logoutButtonText: { color: '#FFF', fontSize: font.base, fontWeight: '700' },
});
