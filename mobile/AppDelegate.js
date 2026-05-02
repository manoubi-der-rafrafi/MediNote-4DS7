import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { NavigationContainer } from '@react-navigation/native';
import { Text, StatusBar, View } from 'react-native';
import { colors } from './src/theme';
import FloatingChat from './src/components/FloatingChat';

import FeedScreen from './src/screens/FeedScreen';
import SaisieScreen from './src/screens/SaisieScreen';
import BriefScreen from './src/screens/BriefScreen';
import ScoreScreen from './src/screens/ScoreScreen';
import SettingsDelegateScreen from './src/screens/SettingsDelegateScreen';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

const TABS = [
  { name: 'Feed',         label: 'Dashboard',    icon: '🏠' },
  { name: 'Saisie',       label: 'Saisie',       icon: '📝' },
  { name: 'Brief',        label: 'Brief',        icon: '📋' },
  { name: 'Score',        label: 'Score',        icon: '📊' },
  { name: 'Parametres',   label: 'Paramètres',   icon: '⚙️' },
];

function DelegateStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Feed" component={FeedScreen} />
      <Stack.Screen name="Saisie" component={SaisieScreen} />
      <Stack.Screen name="Brief" component={BriefScreen} />
    </Stack.Navigator>
  );
}

export default function AppDelegate({ onLogout }) {
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
          tabBarActiveTintColor: colors.green,
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
        <Tab.Screen name="Feed" component={DelegateStack} options={{ tabBarLabel: 'Dashboard' }} />
        <Tab.Screen name="Saisie" component={SaisieScreen} options={{ tabBarLabel: 'Saisie' }} />
        <Tab.Screen name="Brief" component={BriefScreen} options={{ tabBarLabel: 'Brief' }} />
        <Tab.Screen name="Score" component={ScoreScreen} options={{ tabBarLabel: 'Score' }} />
        <Tab.Screen 
          name="Parametres" 
          options={{ tabBarLabel: 'Paramètres' }}
          listeners={{ tabPress: (e) => {} }}
        >
          {({ navigation }) => (
            <SettingsDelegateScreen navigation={navigation} onLogout={onLogout} />
          )}
        </Tab.Screen>
      </Tab.Navigator>
    </NavigationContainer>
    <FloatingChat role="delegate" visitId={541} />
    </View>
  );
}