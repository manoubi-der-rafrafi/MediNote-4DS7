// ─── AppMedecin.js — Médecin CRM Pharma ──────────────────────────────────────────────
import React from 'react';
import { StatusBar, Text, View } from 'react-native';
import FloatingChat from './src/components/FloatingChat';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import { colors } from './src/theme';
import ProfilMedecinScreen      from './src/screens/ProfilMedecinScreen';
import HistoriqueVisitesScreen   from './src/screens/HistoriqueVisitesScreen';
import SettingsMedecinScreen     from './src/screens/SettingsMedecinScreen';

const Tab   = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

const TABS = [
  { name: 'ProfilMedecin',      label: 'Profil Médecin', icon: '👨‍⚕️' },
  { name: 'HistoriqueVisites',  label: 'Historique',     icon: '📋' },
  { name: 'Parametres',         label: 'Paramètres',     icon: '⚙️' },
];

function MedecinStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="ProfilMedecin"     component={ProfilMedecinScreen} />
      <Stack.Screen name="HistoriqueVisites" component={HistoriqueVisitesScreen} />
    </Stack.Navigator>
  );
}

export default function AppMedecin({ onLogout }) {
  return (
    <View style={{ flex: 1 }}>
    <NavigationContainer>
      <StatusBar barStyle="light-content" backgroundColor={colors.bg} />
      <Tab.Navigator
        screenOptions={({ route }) => ({
          headerShown: false,
          tabBarStyle: {
            backgroundColor: colors.s2,
            borderTopColor: colors.bd,
            borderTopWidth: 1,
            height: 56,
            paddingBottom: 6,
          },
          tabBarActiveTintColor:   colors.teal,
          tabBarInactiveTintColor: colors.t3,
          tabBarLabelStyle: { fontSize: 9, fontWeight: '600' },
          tabBarIcon: ({ focused }) => {
            const t = TABS.find(t => t.name === route.name);
            return (
              <Text style={{ fontSize: 16, opacity: focused ? 1 : 0.45 }}>
                {t?.icon}
              </Text>
            );
          },
        })}
      >
        <Tab.Screen name="ProfilMedecin"     component={MedecinStack}            options={{ tabBarLabel: 'Profil Médecin' }} />
        <Tab.Screen name="HistoriqueVisites" component={HistoriqueVisitesScreen} options={{ tabBarLabel: 'Historique' }} />
        <Tab.Screen 
          name="Parametres" 
          options={{ tabBarLabel: 'Paramètres' }}
          listeners={{ tabPress: (e) => {} }}
        >
          {({ navigation }) => (
            <SettingsMedecinScreen navigation={navigation} onLogout={onLogout} />
          )}
        </Tab.Screen>
      </Tab.Navigator>
    </NavigationContainer>
    <FloatingChat role="delegate" visitId={541} />
    </View>
  );
}
