// ─── context/ProfileContext.js — User Profile State Management ──────────────
import React, { createContext, useState, useCallback } from 'react';

export const ProfileContext = createContext({
  profile: {},
  notifications: {},
  security: {},
  updateProfile: () => {},
  changePassword: () => {},
  updateNotificationSettings: () => {},
  enableTwoFactor: () => {},
});

export function ProfileProvider({ children }) {
  const [profile, setProfile] = useState({
    id: 'user123',
    name: 'User',
    email: 'user@pharma.com',
    role: 'delegate', // 'delegate', 'medecin', 'pharmacie'
    avatar: '👤',
    company: 'Pharma Solutions',
    phone: '+212 6XX XXX XXX',
    region: 'Casablanca',
    joinDate: '01/01/2024',
  });

  const [notifications, setNotifications] = useState({
    emailAlerts: true,
    pushNotifications: true,
    weeklyReport: true,
  });

  const [security, setSecurity] = useState({
    twoFactorEnabled: false,
    lastPasswordChange: '15/03/2026',
  });

  const updateProfile = useCallback((updates) => {
    setProfile((prev) => ({ ...prev, ...updates }));
  }, []);

  const changePassword = useCallback((oldPassword, newPassword) => {
    // In a real app, validate with backend
    if (oldPassword && newPassword) {
      setSecurity((prev) => ({
        ...prev,
        lastPasswordChange: new Date().toLocaleDateString('fr-FR'),
      }));
      return true;
    }
    return false;
  }, []);

  const updateNotificationSettings = useCallback((settings) => {
    setNotifications((prev) => ({ ...prev, ...settings }));
  }, []);

  const enableTwoFactor = useCallback((enabled) => {
    setSecurity((prev) => ({ ...prev, twoFactorEnabled: enabled }));
  }, []);

  return (
    <ProfileContext.Provider
      value={{
        profile,
        notifications,
        security,
        updateProfile,
        changePassword,
        updateNotificationSettings,
        enableTwoFactor,
      }}
    >
      {children}
    </ProfileContext.Provider>
  );
}
