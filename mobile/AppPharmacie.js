// ─── AppPharmacie.js — Pharmacie CRM Pharma ───────────────────────────────────────────
import React from 'react';
import { StatusBar, Text, View } from 'react-native';
import FloatingChat from './src/components/FloatingChat';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import { colors } from './src/theme';
import AlertesStockScreen      from './src/screens/AlertesStockScreen';
import AnalysePharmacienScreen from './src/screens/AnalysePharmacienScreen';
import SettingsPharmacieScreen from './src/screens/SettingsPharmacieScreen';

const Tab   = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

const TABS = [
  { name: 'AlertesStock',      label: 'Alertes',   icon: '🔔' },
  { name: 'AnalysePharmacien', label: 'Analyse',   icon: '📊' },
  { name: 'Parametres',        label: 'Paramètres', icon: '⚙️' },
];

function PharmacieStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="AlertesStock"       component={AlertesStockScreen} />
      <Stack.Screen name="AnalysePharmacien"  component={AnalysePharmacienScreen} />
    </Stack.Navigator>
  );
}

export default function AppPharmacie({ onLogout }) {
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
          tabBarActiveTintColor:   colors.gold,
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
        <Tab.Screen name="AlertesStock"      component={PharmacieStack}          options={{ tabBarLabel: 'Alertes'  }} />
        <Tab.Screen name="AnalysePharmacien" component={AnalysePharmacienScreen} options={{ tabBarLabel: 'Analyse'  }} />
        <Tab.Screen 
          name="Parametres" 
          options={{ tabBarLabel: 'Paramètres' }}
          listeners={{ tabPress: (e) => {} }}
        >
          {({ navigation }) => (
            <SettingsPharmacieScreen navigation={navigation} onLogout={onLogout} />
          )}
        </Tab.Screen>
      </Tab.Navigator>
    </NavigationContainer>
    <FloatingChat role="pharmacy" visitId={541} />
    </View>
  );
}
