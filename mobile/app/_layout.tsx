import { useEffect } from "react";
import { Slot, useRouter, useSegments } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { api } from "../lib/api";

export default function RootLayout() {
  const router = useRouter();
  const segments = useSegments();

  useEffect(() => {
    async function bootstrap() {
      await api.init();

      // If not authenticated and not already on an auth screen, redirect.
      // For now the app is open — auth gating can be added later.
    }
    bootstrap();
  }, []);

  return (
    <SafeAreaProvider>
      <StatusBar style="auto" />
      <Slot />
    </SafeAreaProvider>
  );
}
