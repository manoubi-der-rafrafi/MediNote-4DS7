// ─── AppRoot.tsx — Unified Entry Point with Multi-Mode Support ──────────────
import React, { useState, useCallback } from 'react';
import { LogBox } from 'react-native';
import { NavigationIndependentTree } from '@react-navigation/native';

LogBox.ignoreLogs([
  'Non-serializable values were found in the navigation state',
  'VirtualizedLists should never be nested',
  'Warning: Each child in a list',
  'Sending `onAnimatedValueUpdate`',
  'new NativeEventEmitter',
  'EventEmitter.removeListener',
]);
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { SessionProvider } from './src/context/SessionContext';
import { ProfileProvider } from './src/context/ProfileContext';
import LoginScreen from './src/screens/LoginScreen';
import AppMedecinContent from './AppMedecin';
import AppPharmacieContent from './AppPharmacie';
import AppDelegateContent from './AppDelegate';

export default function AppRoot() {
  const [userMode, setUserMode] = useState('delegate');
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const handleLogout = useCallback(() => {
    setIsAuthenticated(false);
    setUserMode('delegate');
  }, []);

  const handleLoginSuccess = useCallback(() => {
    setIsAuthenticated(true);
  }, []);

  const handleModeSelect = useCallback((mode) => {
    setUserMode(mode);
  }, []);

  return (
    <SafeAreaProvider>
      <SessionProvider>
        <ProfileProvider>
          {!isAuthenticated ? (
            <LoginScreen
              onLoginSuccess={handleLoginSuccess}
              onModeSelect={handleModeSelect}
            />
           ) : userMode === 'medecin' ? (
            <NavigationIndependentTree>
              <AppMedecinContent key="medecin" onLogout={handleLogout} />
            </NavigationIndependentTree>
          ) : userMode === 'pharmacie' ? (
            <NavigationIndependentTree>
              <AppPharmacieContent key="pharmacie" onLogout={handleLogout} />
            </NavigationIndependentTree>
          ) : (
            <NavigationIndependentTree>
              <AppDelegateContent key="delegate" onLogout={handleLogout} />
            </NavigationIndependentTree>
          )}
        </ProfileProvider>
      </SessionProvider>
    </SafeAreaProvider>
  );
}
