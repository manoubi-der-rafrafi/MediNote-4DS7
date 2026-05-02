// DISABLED: This file is not used. Entry point is AppRoot.tsx via index.ts.
// Keeping for reference. Use AppRoot.tsx for the React Native app.
export default function App() { return null; }

// ── Bottom tab navigator ──────────────────────────────────────────────────────
function TabNavigatorContent({ onLogout }) {
  const insets = useSafeAreaInsets();
  
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarStyle: {
          backgroundColor: colors.s2,
          borderTopColor: colors.bd,
          borderTopWidth: 1,
          height: 56 + insets.bottom,
          paddingBottom: 8 + insets.bottom,
          paddingTop: 4,
        },
        tabBarActiveTintColor:   colors.blue,
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
      {/* Feed tab uses its own stack so Brief/Saisie/Score are reachable */}
      <Tab.Screen
        name="Feed"
        component={FeedStack}
        options={{ tabBarLabel: 'Accueil' }}
      />
      <Tab.Screen
        name="Brief"
        component={BriefScreen}
        options={{ tabBarLabel: 'Brief' }}
      />
      <Tab.Screen
        name="Saisie"
        component={SaisieScreen}
        options={{ tabBarLabel: 'Saisie' }}
      />
      <Tab.Screen
        name="Score"
        component={ScoreScreen}
        options={{ tabBarLabel: 'Mon score' }}
      />
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
  );
}

export default function App({ onLogout }) {
  return (
    <SafeAreaProvider>
      <AppContent onLogout={onLogout} />
    </SafeAreaProvider>
  );
}

function AppContent({ onLogout }) {
  return (
    <NavigationContainer>
      <StatusBar barStyle="light-content" backgroundColor={colors.bg} />
      <TabNavigatorContent onLogout={onLogout} />
    </NavigationContainer>
  );
}

