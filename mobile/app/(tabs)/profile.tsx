import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  View,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useFocusEffect } from "expo-router";
import type { User } from "../../lib/types";
import { api } from "../../lib/api";

// ── Types ────────────────────────────────────────────────────────

interface SettingsSection {
  title: string;
  items: SettingsItem[];
}

interface SettingsItem {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  type: "navigate" | "toggle" | "action" | "info";
  value?: string | boolean;
  onPress?: () => void;
  onToggle?: (value: boolean) => void;
}

// ── Component ────────────────────────────────────────────────────

export default function ProfileScreen() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncConnected, setSyncConnected] = useState(false);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [darkMode, setDarkMode] = useState(false);

  const loadProfile = useCallback(async () => {
    try {
      const [me, syncStatus] = await Promise.all([
        api.getMe(),
        api.getSyncStatus(),
      ]);
      setUser(me);
      setSyncConnected(syncStatus.google_connected);
    } catch {
      // Offline — show cached or empty
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      loadProfile();
    }, [loadProfile]),
  );

  const handleLogout = useCallback(() => {
    Alert.alert("Log Out", "Are you sure you want to log out?", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Log Out",
        style: "destructive",
        onPress: async () => {
          await api.clearTokens();
          // In a real app, navigate to auth screen
          setUser(null);
        },
      },
    ]);
  }, []);

  const handleSyncNow = useCallback(async () => {
    try {
      await api.triggerSync();
      Alert.alert("Sync", "Calendar sync triggered successfully.");
    } catch {
      Alert.alert("Sync Error", "Could not trigger sync. Try again later.");
    }
  }, []);

  const sections: SettingsSection[] = [
    {
      title: "Schedule",
      items: [
        {
          icon: "calendar-outline",
          label: "Availability",
          type: "navigate",
          onPress: () => {
            // Navigate to availability editor
          },
        },
        {
          icon: "settings-outline",
          label: "Scheduling Rules",
          type: "navigate",
          onPress: () => {
            // Navigate to rules editor
          },
        },
        {
          icon: "book-outline",
          label: "Courses",
          type: "navigate",
          onPress: () => {
            // Navigate to courses list
          },
        },
        {
          icon: "pricetags-outline",
          label: "Tags",
          type: "navigate",
          onPress: () => {
            // Navigate to tags manager
          },
        },
      ],
    },
    {
      title: "Sync",
      items: [
        {
          icon: "logo-google",
          label: "Google Calendar",
          type: "info",
          value: syncConnected ? "Connected" : "Not connected",
        },
        {
          icon: "sync-outline",
          label: "Sync Now",
          type: "action",
          onPress: handleSyncNow,
        },
      ],
    },
    {
      title: "Preferences",
      items: [
        {
          icon: "notifications-outline",
          label: "Notifications",
          type: "toggle",
          value: notificationsEnabled,
          onToggle: setNotificationsEnabled,
        },
        {
          icon: "moon-outline",
          label: "Dark Mode",
          type: "toggle",
          value: darkMode,
          onToggle: setDarkMode,
        },
      ],
    },
    {
      title: "Account",
      items: [
        {
          icon: "shield-checkmark-outline",
          label: "Privacy Policy",
          type: "navigate",
          onPress: () => {},
        },
        {
          icon: "document-text-outline",
          label: "Terms of Service",
          type: "navigate",
          onPress: () => {},
        },
        {
          icon: "information-circle-outline",
          label: "Version",
          type: "info",
          value: "0.1.0",
        },
        {
          icon: "log-out-outline",
          label: "Log Out",
          type: "action",
          onPress: handleLogout,
        },
      ],
    },
  ];

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#4F46E5" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Profile Header */}
      <View style={styles.profileHeader}>
        <View style={styles.avatarLarge}>
          {user?.avatar_url ? (
            <Text style={styles.avatarInitial}>
              {user.display_name?.charAt(0).toUpperCase() || "?"}
            </Text>
          ) : (
            <Text style={styles.avatarInitial}>
              {user?.display_name?.charAt(0).toUpperCase() || "?"}
            </Text>
          )}
        </View>
        <Text style={styles.displayName}>
          {user?.display_name || "Guest"}
        </Text>
        <Text style={styles.email}>{user?.email || "Not signed in"}</Text>
        {user?.timezone && (
          <Text style={styles.timezone}>{user.timezone}</Text>
        )}
      </View>

      {/* Settings Sections */}
      {sections.map((section) => (
        <View key={section.title} style={styles.section}>
          <Text style={styles.sectionTitle}>{section.title}</Text>
          <View style={styles.sectionCard}>
            {section.items.map((item, idx) => (
              <Pressable
                key={item.label}
                style={[
                  styles.settingsRow,
                  idx < section.items.length - 1 && styles.settingsRowBorder,
                ]}
                onPress={item.onPress}
                disabled={item.type === "toggle" || item.type === "info"}
              >
                <Ionicons
                  name={item.icon}
                  size={20}
                  color={item.label === "Log Out" ? "#EF4444" : "#6B7280"}
                  style={styles.settingsIcon}
                />
                <Text
                  style={[
                    styles.settingsLabel,
                    item.label === "Log Out" && styles.logoutLabel,
                  ]}
                >
                  {item.label}
                </Text>

                {item.type === "toggle" && (
                  <Switch
                    value={item.value as boolean}
                    onValueChange={item.onToggle}
                    trackColor={{ false: "#D1D5DB", true: "#A5B4FC" }}
                    thumbColor={item.value ? "#4F46E5" : "#F9FAFB"}
                  />
                )}

                {item.type === "info" && (
                  <Text style={styles.settingsValue}>
                    {String(item.value)}
                  </Text>
                )}

                {item.type === "navigate" && (
                  <Ionicons
                    name="chevron-forward"
                    size={18}
                    color="#D1D5DB"
                  />
                )}
              </Pressable>
            ))}
          </View>
        </View>
      ))}
    </ScrollView>
  );
}

// ── Styles ───────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F9FAFB",
  },
  content: {
    paddingBottom: 40,
  },
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#F9FAFB",
  },

  // Profile header
  profileHeader: {
    alignItems: "center",
    paddingVertical: 32,
    backgroundColor: "#FFFFFF",
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "#E5E7EB",
  },
  avatarLarge: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: "#4F46E5",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 12,
  },
  avatarInitial: {
    fontSize: 32,
    fontWeight: "700",
    color: "#FFFFFF",
  },
  displayName: {
    fontSize: 22,
    fontWeight: "700",
    color: "#111827",
  },
  email: {
    fontSize: 14,
    color: "#6B7280",
    marginTop: 4,
  },
  timezone: {
    fontSize: 13,
    color: "#9CA3AF",
    marginTop: 2,
  },

  // Sections
  section: {
    marginTop: 24,
    paddingHorizontal: 16,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: "600",
    color: "#6B7280",
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: 8,
    marginLeft: 4,
  },
  sectionCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    overflow: "hidden",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  settingsRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  settingsRowBorder: {
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "#F3F4F6",
  },
  settingsIcon: {
    marginRight: 12,
  },
  settingsLabel: {
    flex: 1,
    fontSize: 15,
    color: "#111827",
  },
  logoutLabel: {
    color: "#EF4444",
  },
  settingsValue: {
    fontSize: 14,
    color: "#9CA3AF",
  },
});
