import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useFocusEffect } from "expo-router";
import type { StudyBlock } from "../../lib/types";
import { api } from "../../lib/api";

// ── Helpers ──────────────────────────────────────────────────────

const HOUR_HEIGHT = 60;
const TIMELINE_START_HOUR = 6; // 6 AM
const TIMELINE_END_HOUR = 24; // midnight
const VISIBLE_HOURS = TIMELINE_END_HOUR - TIMELINE_START_HOUR;

function getWeekDates(reference: Date): Date[] {
  const day = reference.getDay(); // 0=Sun
  const monday = new Date(reference);
  monday.setDate(reference.getDate() - ((day + 6) % 7)); // shift to Monday
  monday.setHours(0, 0, 0, 0);

  const dates: Date[] = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    dates.push(d);
  }
  return dates;
}

function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

const DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const MONTH_NAMES = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

// ── Component ────────────────────────────────────────────────────

export default function CalendarScreen() {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [weekDates, setWeekDates] = useState<Date[]>(getWeekDates(new Date()));
  const [blocks, setBlocks] = useState<StudyBlock[]>([]);
  const [loading, setLoading] = useState(true);
  const scrollRef = useRef<ScrollView>(null);

  const loadBlocks = useCallback(async () => {
    try {
      const weekStart = weekDates[0];
      const weekEnd = new Date(weekDates[6]);
      weekEnd.setDate(weekEnd.getDate() + 1);

      const data = await api.getBlocks(
        weekStart.toISOString(),
        weekEnd.toISOString(),
      );
      setBlocks(data);
    } catch {
      // Offline — show empty
    } finally {
      setLoading(false);
    }
  }, [weekDates]);

  useFocusEffect(
    useCallback(() => {
      loadBlocks();
    }, [loadBlocks]),
  );

  // Scroll to current hour on mount
  useEffect(() => {
    const now = new Date();
    const hourOffset = Math.max(0, now.getHours() - TIMELINE_START_HOUR - 1);
    setTimeout(() => {
      scrollRef.current?.scrollTo({ y: hourOffset * HOUR_HEIGHT, animated: false });
    }, 100);
  }, []);

  const navigateWeek = (direction: -1 | 1) => {
    const ref = new Date(weekDates[0]);
    ref.setDate(ref.getDate() + direction * 7);
    const newWeek = getWeekDates(ref);
    setWeekDates(newWeek);
    // Keep selected day in new week if possible, otherwise pick same weekday
    const dayIdx = weekDates.findIndex((d) => isSameDay(d, selectedDate));
    setSelectedDate(newWeek[dayIdx >= 0 ? dayIdx : 0]);
    setLoading(true);
  };

  const dayBlocks = blocks.filter((b) =>
    isSameDay(new Date(b.start), selectedDate),
  );

  return (
    <View style={styles.container}>
      {/* Week Navigation */}
      <View style={styles.weekNav}>
        <Pressable onPress={() => navigateWeek(-1)} style={styles.navButton}>
          <Text style={styles.navButtonText}>{"<"}</Text>
        </Pressable>
        <Text style={styles.weekLabel}>
          {MONTH_NAMES[weekDates[0].getMonth()]} {weekDates[0].getDate()} -{" "}
          {MONTH_NAMES[weekDates[6].getMonth()]} {weekDates[6].getDate()}
        </Text>
        <Pressable onPress={() => navigateWeek(1)} style={styles.navButton}>
          <Text style={styles.navButtonText}>{">"}</Text>
        </Pressable>
      </View>

      {/* Week Strip */}
      <View style={styles.weekStrip}>
        {weekDates.map((date, idx) => {
          const isSelected = isSameDay(date, selectedDate);
          const isToday = isSameDay(date, new Date());
          const hasBlocks = blocks.some((b) =>
            isSameDay(new Date(b.start), date),
          );

          return (
            <Pressable
              key={idx}
              style={[
                styles.dayCell,
                isSelected && styles.dayCellSelected,
                isToday && !isSelected && styles.dayCellToday,
              ]}
              onPress={() => setSelectedDate(date)}
            >
              <Text
                style={[
                  styles.dayName,
                  isSelected && styles.dayTextSelected,
                ]}
              >
                {DAY_NAMES[idx]}
              </Text>
              <Text
                style={[
                  styles.dayNumber,
                  isSelected && styles.dayTextSelected,
                ]}
              >
                {date.getDate()}
              </Text>
              {hasBlocks && (
                <View
                  style={[
                    styles.dayDot,
                    isSelected && styles.dayDotSelected,
                  ]}
                />
              )}
            </Pressable>
          );
        })}
      </View>

      {/* Day Timeline */}
      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#4F46E5" />
        </View>
      ) : (
        <ScrollView ref={scrollRef} style={styles.timeline}>
          <View style={{ height: VISIBLE_HOURS * HOUR_HEIGHT }}>
            {/* Hour lines */}
            {Array.from({ length: VISIBLE_HOURS }, (_, i) => {
              const hour = TIMELINE_START_HOUR + i;
              return (
                <View key={hour} style={[styles.hourRow, { top: i * HOUR_HEIGHT }]}>
                  <Text style={styles.hourLabel}>
                    {hour.toString().padStart(2, "0")}:00
                  </Text>
                  <View style={styles.hourLine} />
                </View>
              );
            })}

            {/* Now indicator */}
            {isSameDay(selectedDate, new Date()) && (() => {
              const now = new Date();
              const minutesSinceStart =
                (now.getHours() - TIMELINE_START_HOUR) * 60 + now.getMinutes();
              if (minutesSinceStart < 0) return null;
              const top = (minutesSinceStart / 60) * HOUR_HEIGHT;
              return (
                <View style={[styles.nowLine, { top }]}>
                  <View style={styles.nowDot} />
                  <View style={styles.nowBar} />
                </View>
              );
            })()}

            {/* Study block cards */}
            {dayBlocks.map((block) => {
              const startDate = new Date(block.start);
              const endDate = new Date(block.end);
              const startMinutes =
                (startDate.getHours() - TIMELINE_START_HOUR) * 60 +
                startDate.getMinutes();
              const durationMinutes =
                (endDate.getTime() - startDate.getTime()) / 60_000;
              const top = (startMinutes / 60) * HOUR_HEIGHT;
              const height = (durationMinutes / 60) * HOUR_HEIGHT;

              return (
                <View
                  key={block.id}
                  style={[
                    styles.blockCard,
                    {
                      top,
                      height: Math.max(height, 24),
                      backgroundColor: block.course_color || "#6366F1",
                    },
                  ]}
                >
                  <Text style={styles.blockCardTitle} numberOfLines={1}>
                    {block.task_title}
                  </Text>
                  <Text style={styles.blockCardTime}>
                    {formatTime(block.start)} - {formatTime(block.end)}
                  </Text>
                </View>
              );
            })}
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
  },
  weekNav: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: "#FFFFFF",
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "#E5E7EB",
  },
  navButton: {
    padding: 8,
  },
  navButtonText: {
    fontSize: 18,
    fontWeight: "600",
    color: "#4F46E5",
  },
  weekLabel: {
    fontSize: 15,
    fontWeight: "600",
    color: "#111827",
  },
  weekStrip: {
    flexDirection: "row",
    backgroundColor: "#FFFFFF",
    paddingVertical: 8,
    paddingHorizontal: 4,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "#E5E7EB",
  },
  dayCell: {
    flex: 1,
    alignItems: "center",
    paddingVertical: 8,
    borderRadius: 10,
    marginHorizontal: 2,
  },
  dayCellSelected: {
    backgroundColor: "#4F46E5",
  },
  dayCellToday: {
    backgroundColor: "#EEF2FF",
  },
  dayName: {
    fontSize: 11,
    fontWeight: "500",
    color: "#6B7280",
    marginBottom: 4,
  },
  dayNumber: {
    fontSize: 16,
    fontWeight: "600",
    color: "#111827",
  },
  dayTextSelected: {
    color: "#FFFFFF",
  },
  dayDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    backgroundColor: "#4F46E5",
    marginTop: 4,
  },
  dayDotSelected: {
    backgroundColor: "#FFFFFF",
  },
  timeline: {
    flex: 1,
    paddingLeft: 56,
    paddingRight: 12,
    paddingTop: 8,
  },
  hourRow: {
    position: "absolute",
    left: -52,
    right: 0,
    flexDirection: "row",
    alignItems: "flex-start",
  },
  hourLabel: {
    width: 44,
    fontSize: 11,
    color: "#9CA3AF",
    textAlign: "right",
    marginRight: 8,
    marginTop: -6,
  },
  hourLine: {
    flex: 1,
    height: StyleSheet.hairlineWidth,
    backgroundColor: "#E5E7EB",
  },
  nowLine: {
    position: "absolute",
    left: -52,
    right: 0,
    flexDirection: "row",
    alignItems: "center",
    zIndex: 10,
  },
  nowDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#EF4444",
    marginLeft: 44,
  },
  nowBar: {
    flex: 1,
    height: 2,
    backgroundColor: "#EF4444",
  },
  blockCard: {
    position: "absolute",
    left: 0,
    right: 0,
    borderRadius: 8,
    padding: 6,
    overflow: "hidden",
  },
  blockCardTitle: {
    fontSize: 13,
    fontWeight: "600",
    color: "#FFFFFF",
  },
  blockCardTime: {
    fontSize: 11,
    color: "rgba(255,255,255,0.85)",
    marginTop: 2,
  },
});
