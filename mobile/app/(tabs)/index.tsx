import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useFocusEffect } from "expo-router";
import type { StudyBlock, Task } from "../../lib/types";
import { api } from "../../lib/api";

// ── Helpers ──────────────────────────────────────────────────────

function todayRange(): { start: string; end: string } {
  const now = new Date();
  const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const endOfDay = new Date(startOfDay.getTime() + 24 * 60 * 60 * 1000);
  return {
    start: startOfDay.toISOString(),
    end: endOfDay.toISOString(),
  };
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function minutesBetween(a: string, b: string): number {
  return Math.round(
    (new Date(b).getTime() - new Date(a).getTime()) / 60_000,
  );
}

// ── Component ────────────────────────────────────────────────────

export default function HomeScreen() {
  const [blocks, setBlocks] = useState<StudyBlock[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const { start, end } = todayRange();
      const [blocksData, tasksData] = await Promise.all([
        api.getBlocks(start, end),
        api.listTasks({ status: "active" }),
      ]);
      setBlocks(
        blocksData.sort(
          (a, b) => new Date(a.start).getTime() - new Date(b.start).getTime(),
        ),
      );
      setTasks(tasksData);
    } catch {
      // Offline — show cached data or empty state
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      loadData();
    }, [loadData]),
  );

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadData();
  }, [loadData]);

  // Derived stats
  const now = new Date();
  const currentBlock = blocks.find(
    (b) => new Date(b.start) <= now && new Date(b.end) > now,
  );
  const upcomingBlocks = blocks.filter((b) => new Date(b.start) > now);
  const completedBlocks = blocks.filter((b) => new Date(b.end) <= now);
  const totalMinutesToday = blocks.reduce(
    (sum, b) => sum + minutesBetween(b.start, b.end),
    0,
  );
  const completedMinutes = completedBlocks.reduce(
    (sum, b) => sum + minutesBetween(b.start, b.end),
    0,
  );
  const dueSoonTasks = tasks.filter((t) => {
    const due = new Date(t.due_date);
    const threeDays = new Date(now.getTime() + 3 * 24 * 60 * 60 * 1000);
    return due <= threeDays;
  });

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#4F46E5" />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Greeting */}
      <Text style={styles.greeting}>
        {now.getHours() < 12
          ? "Good morning"
          : now.getHours() < 18
            ? "Good afternoon"
            : "Good evening"}
      </Text>
      <Text style={styles.date}>
        {now.toLocaleDateString(undefined, {
          weekday: "long",
          month: "long",
          day: "numeric",
        })}
      </Text>

      {/* Quick Stats */}
      <View style={styles.statsRow}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{tasks.length}</Text>
          <Text style={styles.statLabel}>Active Tasks</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{blocks.length}</Text>
          <Text style={styles.statLabel}>Blocks Today</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>
            {Math.round(completedMinutes / 60 * 10) / 10}h
          </Text>
          <Text style={styles.statLabel}>Studied</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>
            {Math.round(totalMinutesToday / 60 * 10) / 10}h
          </Text>
          <Text style={styles.statLabel}>Planned</Text>
        </View>
      </View>

      {/* Current Block */}
      {currentBlock && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Studying Now</Text>
          <View
            style={[
              styles.blockCard,
              styles.currentBlockCard,
              { borderLeftColor: currentBlock.course_color || "#4F46E5" },
            ]}
          >
            <Text style={styles.blockTitle}>{currentBlock.task_title}</Text>
            <Text style={styles.blockMeta}>
              {currentBlock.course_name} | {formatTime(currentBlock.start)} -{" "}
              {formatTime(currentBlock.end)}
            </Text>
            <View style={styles.progressBarBg}>
              <View
                style={[
                  styles.progressBarFg,
                  {
                    width: `${Math.min(
                      100,
                      ((now.getTime() - new Date(currentBlock.start).getTime()) /
                        (new Date(currentBlock.end).getTime() -
                          new Date(currentBlock.start).getTime())) *
                        100,
                    )}%`,
                  },
                ]}
              />
            </View>
          </View>
        </View>
      )}

      {/* Upcoming Blocks */}
      {upcomingBlocks.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Coming Up</Text>
          {upcomingBlocks.slice(0, 5).map((block) => (
            <View
              key={block.id}
              style={[
                styles.blockCard,
                { borderLeftColor: block.course_color || "#6366F1" },
              ]}
            >
              <Text style={styles.blockTitle}>{block.task_title}</Text>
              <Text style={styles.blockMeta}>
                {block.course_name} | {formatTime(block.start)} -{" "}
                {formatTime(block.end)} (
                {minutesBetween(block.start, block.end)} min)
              </Text>
            </View>
          ))}
        </View>
      )}

      {/* Due Soon */}
      {dueSoonTasks.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Due Soon</Text>
          {dueSoonTasks.slice(0, 5).map((task) => (
            <View key={task.id} style={styles.dueSoonCard}>
              <View style={styles.dueSoonRow}>
                <Text style={styles.dueSoonTitle}>{task.title}</Text>
                <Text
                  style={[
                    styles.priorityBadge,
                    {
                      backgroundColor:
                        task.priority === "critical"
                          ? "#EF4444"
                          : task.priority === "high"
                            ? "#F59E0B"
                            : "#6B7280",
                    },
                  ]}
                >
                  {task.priority}
                </Text>
              </View>
              <Text style={styles.dueSoonDate}>
                Due{" "}
                {new Date(task.due_date).toLocaleDateString(undefined, {
                  weekday: "short",
                  month: "short",
                  day: "numeric",
                })}
              </Text>
            </View>
          ))}
        </View>
      )}

      {/* Empty state */}
      {blocks.length === 0 && tasks.length === 0 && (
        <View style={styles.emptyState}>
          <Text style={styles.emptyEmoji}>{"(^_^)"}</Text>
          <Text style={styles.emptyTitle}>All clear!</Text>
          <Text style={styles.emptySubtitle}>
            No tasks or study blocks for today. Add a task to get started.
          </Text>
        </View>
      )}
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
    padding: 16,
    paddingBottom: 32,
  },
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#F9FAFB",
  },
  greeting: {
    fontSize: 28,
    fontWeight: "700",
    color: "#111827",
  },
  date: {
    fontSize: 15,
    color: "#6B7280",
    marginTop: 4,
    marginBottom: 20,
  },
  statsRow: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 24,
  },
  statCard: {
    flex: 1,
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 12,
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  statValue: {
    fontSize: 20,
    fontWeight: "700",
    color: "#4F46E5",
  },
  statLabel: {
    fontSize: 11,
    color: "#6B7280",
    marginTop: 2,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 12,
  },
  blockCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 14,
    marginBottom: 8,
    borderLeftWidth: 4,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  currentBlockCard: {
    borderWidth: 1,
    borderColor: "#C7D2FE",
    backgroundColor: "#EEF2FF",
  },
  blockTitle: {
    fontSize: 15,
    fontWeight: "600",
    color: "#111827",
  },
  blockMeta: {
    fontSize: 13,
    color: "#6B7280",
    marginTop: 4,
  },
  progressBarBg: {
    height: 4,
    backgroundColor: "#E5E7EB",
    borderRadius: 2,
    marginTop: 10,
    overflow: "hidden",
  },
  progressBarFg: {
    height: 4,
    backgroundColor: "#4F46E5",
    borderRadius: 2,
  },
  dueSoonCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 14,
    marginBottom: 8,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  dueSoonRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  dueSoonTitle: {
    fontSize: 15,
    fontWeight: "600",
    color: "#111827",
    flex: 1,
  },
  priorityBadge: {
    fontSize: 11,
    fontWeight: "600",
    color: "#FFFFFF",
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
    overflow: "hidden",
    textTransform: "capitalize",
  },
  dueSoonDate: {
    fontSize: 13,
    color: "#6B7280",
    marginTop: 4,
  },
  emptyState: {
    alignItems: "center",
    paddingTop: 60,
  },
  emptyEmoji: {
    fontSize: 32,
    marginBottom: 12,
    color: "#9CA3AF",
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: "600",
    color: "#111827",
  },
  emptySubtitle: {
    fontSize: 15,
    color: "#6B7280",
    marginTop: 4,
    textAlign: "center",
    paddingHorizontal: 32,
  },
});
