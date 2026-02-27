import React, { useCallback, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Animated,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useFocusEffect } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import type { Task } from "../../lib/types";
import { api } from "../../lib/api";

// ── Helpers ──────────────────────────────────────────────────────

const PRIORITY_COLORS: Record<string, string> = {
  critical: "#EF4444",
  high: "#F59E0B",
  medium: "#3B82F6",
  low: "#6B7280",
};

const FOCUS_LABELS: Record<string, string> = {
  light: "Light",
  medium: "Medium",
  deep: "Deep Focus",
};

function formatDueDate(iso: string): string {
  const due = new Date(iso);
  const now = new Date();
  const diffMs = due.getTime() - now.getTime();
  const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays < 0) return `${Math.abs(diffDays)}d overdue`;
  if (diffDays === 0) return "Due today";
  if (diffDays === 1) return "Due tomorrow";
  if (diffDays <= 7) return `Due in ${diffDays}d`;
  return due.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

// ── Task Row with Swipe Actions ──────────────────────────────────

interface TaskRowProps {
  task: Task;
  onComplete: (id: number) => void;
  onAddTime: (id: number) => void;
}

function TaskRow({ task, onComplete, onAddTime }: TaskRowProps) {
  const isOverdue =
    new Date(task.due_date).getTime() < Date.now() && task.status === "active";
  const dueText = formatDueDate(task.due_date);

  return (
    <View style={styles.taskRow}>
      {/* Swipe hint: left action = complete */}
      <View style={styles.taskContent}>
        <View style={styles.taskHeader}>
          <View
            style={[
              styles.priorityDot,
              { backgroundColor: PRIORITY_COLORS[task.priority] || "#6B7280" },
            ]}
          />
          <Text style={styles.taskTitle} numberOfLines={1}>
            {task.title}
          </Text>
        </View>

        <View style={styles.taskMeta}>
          <Text style={[styles.dueText, isOverdue && styles.overdueText]}>
            {dueText}
          </Text>
          {task.estimated_hours != null && (
            <Text style={styles.metaChip}>
              {task.estimated_hours}h est.
            </Text>
          )}
          <Text style={styles.metaChip}>
            {FOCUS_LABELS[task.focus_load] || task.focus_load}
          </Text>
          <Text style={styles.metaChip}>{task.task_type}</Text>
        </View>
      </View>

      {/* Action buttons (instead of gesture-based swipe for simplicity) */}
      <View style={styles.taskActions}>
        <Pressable
          style={[styles.actionBtn, styles.addTimeBtn]}
          onPress={() => onAddTime(task.id)}
        >
          <Ionicons name="time-outline" size={18} color="#FFFFFF" />
        </Pressable>
        <Pressable
          style={[styles.actionBtn, styles.completeBtn]}
          onPress={() => onComplete(task.id)}
        >
          <Ionicons name="checkmark" size={18} color="#FFFFFF" />
        </Pressable>
      </View>
    </View>
  );
}

// ── Tasks Screen ─────────────────────────────────────────────────

type FilterTab = "active" | "completed" | "archived";

export default function TasksScreen() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<FilterTab>("active");

  const loadTasks = useCallback(async () => {
    try {
      const data = await api.listTasks({ status: filter });
      setTasks(
        data.sort(
          (a, b) =>
            new Date(a.due_date).getTime() - new Date(b.due_date).getTime(),
        ),
      );
    } catch {
      // Offline — use cached data
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filter]);

  useFocusEffect(
    useCallback(() => {
      setLoading(true);
      loadTasks();
    }, [loadTasks]),
  );

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadTasks();
  }, [loadTasks]);

  const handleComplete = useCallback(
    async (taskId: number) => {
      try {
        await Haptics.notificationAsync(
          Haptics.NotificationFeedbackType.Success,
        );
        await api.completeTask(taskId);
        setTasks((prev) => prev.filter((t) => t.id !== taskId));
      } catch {
        Alert.alert("Error", "Could not complete task. Will retry when online.");
      }
    },
    [],
  );

  const handleAddTime = useCallback((taskId: number) => {
    Alert.prompt
      ? Alert.prompt(
          "Add Time",
          "How many additional hours do you need?",
          [
            { text: "Cancel", style: "cancel" },
            {
              text: "Add",
              onPress: async (value?: string) => {
                const hours = parseFloat(value || "0");
                if (hours > 0) {
                  try {
                    await api.addTime(taskId, hours);
                    await Haptics.impactAsync(
                      Haptics.ImpactFeedbackStyle.Light,
                    );
                  } catch {
                    Alert.alert("Error", "Could not add time.");
                  }
                }
              },
            },
          ],
          "plain-text",
          "",
          "decimal-pad",
        )
      : Alert.alert(
          "Add Time",
          "Use the web app to add time to this task.",
        );
  }, []);

  // Group tasks by urgency
  const overdue = tasks.filter(
    (t) => new Date(t.due_date).getTime() < Date.now(),
  );
  const upcoming = tasks.filter(
    (t) => new Date(t.due_date).getTime() >= Date.now(),
  );

  return (
    <View style={styles.container}>
      {/* Filter Tabs */}
      <View style={styles.filterRow}>
        {(["active", "completed", "archived"] as FilterTab[]).map((tab) => (
          <Pressable
            key={tab}
            style={[
              styles.filterTab,
              filter === tab && styles.filterTabActive,
            ]}
            onPress={() => setFilter(tab)}
          >
            <Text
              style={[
                styles.filterTabText,
                filter === tab && styles.filterTabTextActive,
              ]}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </Text>
          </Pressable>
        ))}
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#4F46E5" />
        </View>
      ) : tasks.length === 0 ? (
        <View style={styles.center}>
          <Ionicons name="checkbox-outline" size={48} color="#D1D5DB" />
          <Text style={styles.emptyTitle}>
            No {filter} tasks
          </Text>
          <Text style={styles.emptySubtitle}>
            {filter === "active"
              ? "You're all caught up!"
              : `No ${filter} tasks to show.`}
          </Text>
        </View>
      ) : (
        <ScrollView
          style={styles.list}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        >
          {/* Overdue section */}
          {overdue.length > 0 && filter === "active" && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>
                Overdue ({overdue.length})
              </Text>
              {overdue.map((task) => (
                <TaskRow
                  key={task.id}
                  task={task}
                  onComplete={handleComplete}
                  onAddTime={handleAddTime}
                />
              ))}
            </View>
          )}

          {/* Upcoming / Main list */}
          <View style={styles.section}>
            {overdue.length > 0 && filter === "active" && (
              <Text style={styles.sectionTitle}>
                Upcoming ({upcoming.length})
              </Text>
            )}
            {(filter === "active" ? upcoming : tasks).map((task) => (
              <TaskRow
                key={task.id}
                task={task}
                onComplete={handleComplete}
                onAddTime={handleAddTime}
              />
            ))}
          </View>
        </ScrollView>
      )}
    </View>
  );
}

// ── Styles ───────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F9FAFB",
  },
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 32,
  },
  filterRow: {
    flexDirection: "row",
    backgroundColor: "#FFFFFF",
    padding: 8,
    gap: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "#E5E7EB",
  },
  filterTab: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 8,
    alignItems: "center",
    backgroundColor: "#F3F4F6",
  },
  filterTabActive: {
    backgroundColor: "#4F46E5",
  },
  filterTabText: {
    fontSize: 14,
    fontWeight: "500",
    color: "#6B7280",
  },
  filterTabTextActive: {
    color: "#FFFFFF",
  },
  list: {
    flex: 1,
  },
  listContent: {
    padding: 16,
    paddingBottom: 32,
  },
  section: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: "600",
    color: "#6B7280",
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  taskRow: {
    flexDirection: "row",
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    marginBottom: 8,
    overflow: "hidden",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  taskContent: {
    flex: 1,
    padding: 14,
  },
  taskHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  priorityDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  taskTitle: {
    flex: 1,
    fontSize: 15,
    fontWeight: "600",
    color: "#111827",
  },
  taskMeta: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
    marginTop: 8,
  },
  dueText: {
    fontSize: 12,
    fontWeight: "500",
    color: "#6B7280",
  },
  overdueText: {
    color: "#EF4444",
    fontWeight: "600",
  },
  metaChip: {
    fontSize: 11,
    color: "#6B7280",
    backgroundColor: "#F3F4F6",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    overflow: "hidden",
  },
  taskActions: {
    flexDirection: "row",
  },
  actionBtn: {
    width: 44,
    justifyContent: "center",
    alignItems: "center",
  },
  addTimeBtn: {
    backgroundColor: "#3B82F6",
  },
  completeBtn: {
    backgroundColor: "#10B981",
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#111827",
    marginTop: 12,
  },
  emptySubtitle: {
    fontSize: 14,
    color: "#6B7280",
    marginTop: 4,
    textAlign: "center",
  },
});
