import { Slot } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';

// Use <Slot> instead of <Stack> — AppRoot manages its own NavigationContainer
// so we must NOT add another native stack here (causes RNSScreen crash)
export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <StatusBar style="light" backgroundColor="#10817E" />
      <Slot />
    </SafeAreaProvider>
  );
}
