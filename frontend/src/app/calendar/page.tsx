"use client";

import { Button } from "@/components/ui/button";
import { useBlocks, useGeneratePlan, useConfirmPlan } from "@/lib/hooks";
import { useCalendarStore, useDiffStore } from "@/lib/stores";
import { format, startOfWeek, addDays, addHours } from "date-fns";
import { useMemo } from "react";

const HOURS = Array.from({ length: 15 }, (_, i) => i + 7); // 7am to 9pm

export default function CalendarPage() {
  const { currentDate, nextWeek, prevWeek, today } = useCalendarStore();
  const { data: blocks } = useBlocks();
  const generatePlan = useGeneratePlan();
  const confirmPlan = useConfirmPlan();
  const diffStore = useDiffStore();

  const weekStart = startOfWeek(currentDate, { weekStartsOn: 1 });
  const weekDays = useMemo(
    () => Array.from({ length: 7 }, (_, i) => addDays(weekStart, i)),
    [weekStart]
  );

  const handleReplan = async () => {
    const diff = await generatePlan.mutateAsync("manual_replan");
    diffStore.setDiff(diff);
  };

  const handleConfirm = async () => {
    await confirmPlan.mutateAsync();
    diffStore.close();
  };

  const getBlocksForDayAndHour = (day: Date, hour: number) => {
    return (blocks || []).filter((b) => {
      const start = new Date(b.start);
      return (
        start.toDateString() === day.toDateString() &&
        start.getHours() === hour
      );
    });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-[var(--border)]">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={prevWeek}>
            Prev
          </Button>
          <Button variant="outline" size="sm" onClick={today}>
            Today
          </Button>
          <Button variant="outline" size="sm" onClick={nextWeek}>
            Next
          </Button>
          <h2 className="text-lg font-semibold ml-4">
            {format(weekStart, "MMM d")} - {format(addDays(weekStart, 6), "MMM d, yyyy")}
          </h2>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleReplan} disabled={generatePlan.isPending}>
            {generatePlan.isPending ? "Planning..." : "Generate Plan"}
          </Button>
          {diffStore.diff && (
            <Button variant="secondary" onClick={handleConfirm} disabled={confirmPlan.isPending}>
              Confirm ({diffStore.diff.added} added, {diffStore.diff.moved} moved,{" "}
              {diffStore.diff.deleted} deleted)
            </Button>
          )}
        </div>
      </div>

      {/* Week grid */}
      <div className="flex-1 overflow-auto">
        <div className="grid grid-cols-[60px_repeat(7,1fr)] min-w-[800px]">
          {/* Day headers */}
          <div className="border-b border-[var(--border)] p-2" />
          {weekDays.map((day) => (
            <div
              key={day.toISOString()}
              className="border-b border-l border-[var(--border)] p-2 text-center"
            >
              <div className="text-xs text-[var(--muted-foreground)]">
                {format(day, "EEE")}
              </div>
              <div
                className={`text-lg font-semibold ${
                  day.toDateString() === new Date().toDateString()
                    ? "text-[var(--primary)]"
                    : ""
                }`}
              >
                {format(day, "d")}
              </div>
            </div>
          ))}

          {/* Time rows */}
          {HOURS.map((hour) => (
            <div key={hour} className="contents">
              <div className="border-b border-[var(--border)] p-1 text-xs text-right text-[var(--muted-foreground)] pr-2">
                {hour}:00
              </div>
              {weekDays.map((day) => {
                const dayBlocks = getBlocksForDayAndHour(day, hour);
                return (
                  <div
                    key={`${day.toISOString()}-${hour}`}
                    className="border-b border-l border-[var(--border)] min-h-[60px] relative p-0.5"
                  >
                    {dayBlocks.map((block) => {
                      const start = new Date(block.start);
                      const end = new Date(block.end);
                      const durationMin = (end.getTime() - start.getTime()) / 60000;
                      const height = Math.max(durationMin, 15);
                      const topOffset = start.getMinutes();

                      return (
                        <div
                          key={block.id}
                          className="absolute left-0.5 right-0.5 rounded px-1 py-0.5 text-xs text-white cursor-pointer hover:opacity-80"
                          style={{
                            backgroundColor: block.course_color || "var(--accent)",
                            top: `${topOffset}px`,
                            height: `${height}px`,
                            minHeight: "20px",
                          }}
                          title={`${block.task_title}\n${format(start, "HH:mm")} - ${format(end, "HH:mm")}`}
                        >
                          <span className="font-medium truncate block">
                            {block.task_title}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
