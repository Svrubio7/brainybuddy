"use client";

import { useState, useCallback, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAvailability, useRules } from "@/lib/hooks";
import { api } from "@/lib/api";
import type { AvailabilityGrid, SchedulingRules } from "@/lib/types";

const DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"] as const;
const HOURS = Array.from({ length: 24 }, (_, i) => i);

export default function SettingsPage() {
  const { data: availability } = useAvailability();
  const { data: rules } = useRules();
  const [grid, setGrid] = useState<AvailabilityGrid | null>(null);
  const [localRules, setLocalRules] = useState<SchedulingRules | null>(null);
  const [isPainting, setIsPainting] = useState(false);
  const [paintValue, setPaintValue] = useState(true);

  useEffect(() => {
    if (availability) setGrid(availability);
  }, [availability]);

  useEffect(() => {
    if (rules) setLocalRules(rules);
  }, [rules]);

  const toggleSlot = useCallback(
    (day: typeof DAYS[number], slotIndex: number, value?: boolean) => {
      setGrid((prev) => {
        if (!prev) return prev;
        const newGrid = { ...prev };
        const daySlots = [...newGrid[day]];
        daySlots[slotIndex] = value ?? !daySlots[slotIndex];
        newGrid[day] = daySlots;
        return newGrid;
      });
    },
    []
  );

  const saveGrid = async () => {
    if (grid) await api.updateAvailability(grid);
  };

  const saveRules = async () => {
    if (localRules) await api.updateRules(localRules);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <h1 className="text-2xl font-bold">Settings</h1>

      {/* Availability Grid */}
      <Card>
        <CardHeader>
          <CardTitle>Availability</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-[var(--muted-foreground)] mb-4">
            Click and drag to paint your available time slots (each cell = 1 hour, 4 slots of 15min)
          </p>

          {grid && (
            <div className="overflow-auto">
              <div className="grid grid-cols-[60px_repeat(7,1fr)] gap-px text-xs select-none">
                <div />
                {DAYS.map((d) => (
                  <div key={d} className="text-center font-medium p-1 capitalize">
                    {d.slice(0, 3)}
                  </div>
                ))}

                {HOURS.map((hour) => (
                  <div key={hour} className="contents">
                    <div className="text-right pr-2 py-1 text-[var(--muted-foreground)]">
                      {hour}:00
                    </div>
                    {DAYS.map((day) => {
                      const slotStart = hour * 4;
                      const isAvailable = grid[day]
                        .slice(slotStart, slotStart + 4)
                        .some(Boolean);
                      return (
                        <div
                          key={`${day}-${hour}`}
                          className={`h-6 cursor-pointer border border-[var(--border)] transition-colors ${
                            isAvailable
                              ? "bg-[var(--primary)] opacity-70"
                              : "bg-[var(--secondary)]"
                          }`}
                          onMouseDown={() => {
                            setIsPainting(true);
                            const newVal = !isAvailable;
                            setPaintValue(newVal);
                            for (let i = 0; i < 4; i++) toggleSlot(day, slotStart + i, newVal);
                          }}
                          onMouseEnter={() => {
                            if (isPainting) {
                              for (let i = 0; i < 4; i++) toggleSlot(day, slotStart + i, paintValue);
                            }
                          }}
                          onMouseUp={() => setIsPainting(false)}
                        />
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          )}

          <Button onClick={saveGrid} className="mt-4">
            Save Availability
          </Button>
        </CardContent>
      </Card>

      {/* Scheduling Rules */}
      {localRules && (
        <Card>
          <CardHeader>
            <CardTitle>Scheduling Rules</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Daily Max Hours</label>
                <Input
                  type="number"
                  value={localRules.daily_max_hours}
                  onChange={(e) =>
                    setLocalRules({ ...localRules, daily_max_hours: parseFloat(e.target.value) })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">Weekend Max Hours</label>
                <Input
                  type="number"
                  value={localRules.weekend_max_hours}
                  onChange={(e) =>
                    setLocalRules({ ...localRules, weekend_max_hours: parseFloat(e.target.value) })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">Break After (minutes)</label>
                <Input
                  type="number"
                  value={localRules.break_after_minutes}
                  onChange={(e) =>
                    setLocalRules({ ...localRules, break_after_minutes: parseInt(e.target.value) })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">Break Duration (minutes)</label>
                <Input
                  type="number"
                  value={localRules.break_duration_minutes}
                  onChange={(e) =>
                    setLocalRules({
                      ...localRules,
                      break_duration_minutes: parseInt(e.target.value),
                    })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">Preferred Start Hour</label>
                <Input
                  type="number"
                  min="0"
                  max="23"
                  value={localRules.preferred_start_hour}
                  onChange={(e) =>
                    setLocalRules({ ...localRules, preferred_start_hour: parseInt(e.target.value) })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">Preferred End Hour</label>
                <Input
                  type="number"
                  min="0"
                  max="23"
                  value={localRules.preferred_end_hour}
                  onChange={(e) =>
                    setLocalRules({ ...localRules, preferred_end_hour: parseInt(e.target.value) })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">Sleep Start Hour</label>
                <Input
                  type="number"
                  min="0"
                  max="23"
                  value={localRules.sleep_start_hour}
                  onChange={(e) =>
                    setLocalRules({ ...localRules, sleep_start_hour: parseInt(e.target.value) })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">Sleep End Hour</label>
                <Input
                  type="number"
                  min="0"
                  max="23"
                  value={localRules.sleep_end_hour}
                  onChange={(e) =>
                    setLocalRules({ ...localRules, sleep_end_hour: parseInt(e.target.value) })
                  }
                />
              </div>
            </div>
            <Button onClick={saveRules}>Save Rules</Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
