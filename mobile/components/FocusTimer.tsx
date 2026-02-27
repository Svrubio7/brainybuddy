import React, { useCallback, useEffect, useRef, useState } from "react";
import { Pressable, StyleSheet, Text, Vibration, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";

// ── Types ────────────────────────────────────────────────────────

type TimerState = "idle" | "running" | "paused" | "break";

interface FocusTimerProps {
  /** Currently active task title */
  taskTitle?: string;
  /** Currently active course name */
  courseName?: string;
  /** Course accent color */
  courseColor?: string;
  /** Focus duration in minutes (default 25) */
  focusDuration?: number;
  /** Break duration in minutes (default 5) */
  breakDuration?: number;
  /** Long break duration in minutes (default 15) */
  longBreakDuration?: number;
  /** Sessions before a long break (default 4) */
  sessionsBeforeLongBreak?: number;
  /** Called when a focus session completes */
  onSessionComplete?: (durationMinutes: number) => void;
  /** Called when the timer is stopped manually */
  onStop?: (elapsedMinutes: number) => void;
}

// ── Helpers ──────────────────────────────────────────────────────

function formatTime(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
}

function getProgressAngle(remaining: number, total: number): number {
  if (total <= 0) return 0;
  return ((total - remaining) / total) * 360;
}

// ── Component ────────────────────────────────────────────────────

export default function FocusTimer({
  taskTitle = "No task selected",
  courseName,
  courseColor = "#4F46E5",
  focusDuration = 25,
  breakDuration = 5,
  longBreakDuration = 15,
  sessionsBeforeLongBreak = 4,
  onSessionComplete,
  onStop,
}: FocusTimerProps) {
  const [state, setState] = useState<TimerState>("idle");
  const [remainingSeconds, setRemainingSeconds] = useState(focusDuration * 60);
  const [totalSeconds, setTotalSeconds] = useState(focusDuration * 60);
  const [completedSessions, setCompletedSessions] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Clean up interval on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  // Tick
  useEffect(() => {
    if (state === "running" || state === "break") {
      intervalRef.current = setInterval(() => {
        setRemainingSeconds((prev) => {
          if (prev <= 1) {
            // Timer completed
            clearInterval(intervalRef.current!);
            intervalRef.current = null;
            handleTimerEnd();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
    // We intentionally only re-run when state changes:
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state]);

  const handleTimerEnd = useCallback(() => {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    Vibration.vibrate([0, 250, 100, 250]);

    if (state === "running") {
      // Focus session completed
      const sessions = completedSessions + 1;
      setCompletedSessions(sessions);
      onSessionComplete?.(focusDuration);

      // Start break
      const isLongBreak = sessions % sessionsBeforeLongBreak === 0;
      const breakMins = isLongBreak ? longBreakDuration : breakDuration;
      setTotalSeconds(breakMins * 60);
      setRemainingSeconds(breakMins * 60);
      setState("break");
    } else if (state === "break") {
      // Break completed — go back to idle, ready for next focus
      setTotalSeconds(focusDuration * 60);
      setRemainingSeconds(focusDuration * 60);
      setState("idle");
    }
  }, [
    state,
    completedSessions,
    focusDuration,
    breakDuration,
    longBreakDuration,
    sessionsBeforeLongBreak,
    onSessionComplete,
  ]);

  const handleStart = useCallback(() => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    if (state === "idle") {
      setTotalSeconds(focusDuration * 60);
      setRemainingSeconds(focusDuration * 60);
    }
    setState("running");
  }, [state, focusDuration]);

  const handlePause = useCallback(() => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    setState("paused");
  }, []);

  const handleResume = useCallback(() => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    setState("running");
  }, []);

  const handleStop = useCallback(() => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
    const elapsedSeconds = totalSeconds - remainingSeconds;
    const elapsedMinutes = Math.round(elapsedSeconds / 60);

    if (state === "running" || state === "paused") {
      onStop?.(elapsedMinutes);
    }

    setState("idle");
    setTotalSeconds(focusDuration * 60);
    setRemainingSeconds(focusDuration * 60);
  }, [totalSeconds, remainingSeconds, state, focusDuration, onStop]);

  const handleSkipBreak = useCallback(() => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    setTotalSeconds(focusDuration * 60);
    setRemainingSeconds(focusDuration * 60);
    setState("idle");
  }, [focusDuration]);

  // Progress for the circular ring (simple percentage-based)
  const progress = totalSeconds > 0 ? (totalSeconds - remainingSeconds) / totalSeconds : 0;

  const stateLabel =
    state === "idle"
      ? "Ready"
      : state === "running"
        ? "Focus"
        : state === "paused"
          ? "Paused"
          : "Break";

  const ringColor =
    state === "break" ? "#10B981" : state === "paused" ? "#F59E0B" : courseColor;

  return (
    <View style={styles.container}>
      {/* Task info */}
      <View style={styles.taskInfo}>
        <Text style={styles.taskTitle} numberOfLines={1}>
          {taskTitle}
        </Text>
        {courseName && (
          <View style={styles.courseRow}>
            <View
              style={[styles.courseDot, { backgroundColor: courseColor }]}
            />
            <Text style={styles.courseName}>{courseName}</Text>
          </View>
        )}
      </View>

      {/* Timer display */}
      <View style={styles.timerContainer}>
        {/* Background ring */}
        <View style={styles.ringBg}>
          {/* Progress ring (simplified — full circle progress represented as border) */}
          <View
            style={[
              styles.ringProgress,
              {
                borderColor: ringColor,
                borderRightColor:
                  progress > 0.25 ? ringColor : "transparent",
                borderBottomColor:
                  progress > 0.5 ? ringColor : "transparent",
                borderLeftColor:
                  progress > 0.75 ? ringColor : "transparent",
                transform: [{ rotate: "-90deg" }],
              },
            ]}
          />
          {/* Inner circle with time */}
          <View style={styles.innerCircle}>
            <Text style={styles.stateLabel}>{stateLabel}</Text>
            <Text style={styles.timeDisplay}>
              {formatTime(remainingSeconds)}
            </Text>
            <Text style={styles.sessionCount}>
              Session {completedSessions + 1}
            </Text>
          </View>
        </View>
      </View>

      {/* Controls */}
      <View style={styles.controls}>
        {state === "idle" && (
          <Pressable
            style={[styles.controlBtn, styles.startBtn, { backgroundColor: courseColor }]}
            onPress={handleStart}
          >
            <Ionicons name="play" size={28} color="#FFFFFF" />
            <Text style={styles.controlBtnText}>Start Focus</Text>
          </Pressable>
        )}

        {state === "running" && (
          <View style={styles.controlRow}>
            <Pressable
              style={[styles.controlBtn, styles.secondaryBtn]}
              onPress={handleStop}
            >
              <Ionicons name="stop" size={24} color="#EF4444" />
            </Pressable>
            <Pressable
              style={[styles.controlBtn, styles.pauseBtn]}
              onPress={handlePause}
            >
              <Ionicons name="pause" size={28} color="#FFFFFF" />
              <Text style={styles.controlBtnText}>Pause</Text>
            </Pressable>
          </View>
        )}

        {state === "paused" && (
          <View style={styles.controlRow}>
            <Pressable
              style={[styles.controlBtn, styles.secondaryBtn]}
              onPress={handleStop}
            >
              <Ionicons name="stop" size={24} color="#EF4444" />
            </Pressable>
            <Pressable
              style={[styles.controlBtn, styles.resumeBtn, { backgroundColor: courseColor }]}
              onPress={handleResume}
            >
              <Ionicons name="play" size={28} color="#FFFFFF" />
              <Text style={styles.controlBtnText}>Resume</Text>
            </Pressable>
          </View>
        )}

        {state === "break" && (
          <Pressable
            style={[styles.controlBtn, styles.skipBtn]}
            onPress={handleSkipBreak}
          >
            <Ionicons name="play-skip-forward" size={24} color="#6B7280" />
            <Text style={[styles.controlBtnText, { color: "#6B7280" }]}>
              Skip Break
            </Text>
          </Pressable>
        )}
      </View>

      {/* Session dots */}
      <View style={styles.sessionDots}>
        {Array.from({ length: sessionsBeforeLongBreak }, (_, i) => (
          <View
            key={i}
            style={[
              styles.sessionDot,
              i < completedSessions % sessionsBeforeLongBreak
                ? { backgroundColor: courseColor }
                : styles.sessionDotEmpty,
            ]}
          />
        ))}
      </View>
    </View>
  );
}

// ── Styles ───────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    paddingVertical: 24,
    paddingHorizontal: 16,
  },

  // Task info
  taskInfo: {
    alignItems: "center",
    marginBottom: 24,
  },
  taskTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#111827",
    textAlign: "center",
  },
  courseRow: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 6,
  },
  courseDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  courseName: {
    fontSize: 14,
    color: "#6B7280",
  },

  // Timer ring
  timerContainer: {
    marginBottom: 32,
  },
  ringBg: {
    width: 220,
    height: 220,
    borderRadius: 110,
    backgroundColor: "#F3F4F6",
    justifyContent: "center",
    alignItems: "center",
  },
  ringProgress: {
    position: "absolute",
    width: 220,
    height: 220,
    borderRadius: 110,
    borderWidth: 6,
    borderTopColor: "transparent",
  },
  innerCircle: {
    width: 196,
    height: 196,
    borderRadius: 98,
    backgroundColor: "#FFFFFF",
    justifyContent: "center",
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  stateLabel: {
    fontSize: 13,
    fontWeight: "600",
    color: "#9CA3AF",
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  timeDisplay: {
    fontSize: 48,
    fontWeight: "200",
    color: "#111827",
    fontVariant: ["tabular-nums"],
    marginVertical: 4,
  },
  sessionCount: {
    fontSize: 13,
    color: "#9CA3AF",
  },

  // Controls
  controls: {
    marginBottom: 20,
  },
  controlRow: {
    flexDirection: "row",
    gap: 16,
    alignItems: "center",
  },
  controlBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 14,
    paddingHorizontal: 28,
    borderRadius: 28,
  },
  startBtn: {
    minWidth: 180,
  },
  pauseBtn: {
    backgroundColor: "#F59E0B",
    minWidth: 140,
  },
  resumeBtn: {
    minWidth: 140,
  },
  secondaryBtn: {
    backgroundColor: "#F3F4F6",
    paddingHorizontal: 18,
  },
  skipBtn: {
    backgroundColor: "#F3F4F6",
    minWidth: 160,
  },
  controlBtnText: {
    fontSize: 16,
    fontWeight: "600",
    color: "#FFFFFF",
  },

  // Session dots
  sessionDots: {
    flexDirection: "row",
    gap: 8,
  },
  sessionDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  sessionDotEmpty: {
    backgroundColor: "#E5E7EB",
  },
});
