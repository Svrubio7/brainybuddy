"use client";

import Link from "next/link";
import { useState } from "react";
import {
  IconCheckSquare,
  IconClock,
  IconBook,
  IconPlus,
  IconChat,
  IconSearch,
  IconCalendar,
  IconHelpCircle,
  IconGrid,
  IconList,
  IconFilter,
  IconCheckCircle,
  IconTrash,
} from "@/components/ui/icons";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  useTasks,
  useBlocks,
  useCourses,
  useCompleteTask,
  useDeleteTask,
} from "@/lib/hooks";
import { useChatStore, useAuthStore } from "@/lib/stores";
import type { Task } from "@/lib/types";

type ViewMode = "kanban" | "list";

function priorityVariant(p: string) {
  if (p === "critical") return "critical";
  if (p === "high") return "high";
  if (p === "medium") return "medium";
  return "low";
}

const kanbanColumns = [
  { key: "active", label: "To Do", dotColor: "#6F80FF" },
  { key: "in_progress", label: "In Progress", dotColor: "#FFA500" },
  { key: "completed", label: "Done", dotColor: "#68b266" },
] as const;

function KanbanTaskCard({
  task,
  courseName,
  courseColor,
  onComplete,
  onDelete,
}: {
  task: Task;
  courseName?: string;
  courseColor?: string;
  onComplete: () => void;
  onDelete: () => void;
}) {
  return (
    <Card className="group hover:shadow-md transition-shadow">
      <CardContent className="space-y-2.5">
        <div className="flex items-center justify-between">
          <Badge variant={priorityVariant(task.priority)}>{task.priority}</Badge>
          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {task.status === "active" && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onComplete();
                }}
                className="rounded p-1 text-[var(--muted-foreground)] hover:bg-[var(--muted)] hover:text-[#68b266]"
                title="Complete"
              >
                <IconCheckCircle className="h-3.5 w-3.5" />
              </button>
            )}
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              className="rounded p-1 text-[var(--muted-foreground)] hover:bg-[var(--muted)] hover:text-[var(--destructive)]"
              title="Delete"
            >
              <IconTrash className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        <h4 className="text-sm font-semibold text-[var(--foreground)] leading-tight">
          {task.title}
        </h4>

        {task.description && (
          <p className="text-xs text-[var(--muted-foreground)] line-clamp-2">
            {task.description}
          </p>
        )}

        <div className="flex items-center justify-between text-xs text-[var(--muted-foreground)]">
          <span>
            {new Date(task.due_date).toLocaleDateString(undefined, {
              month: "short",
              day: "numeric",
            })}
          </span>
          <div className="flex items-center gap-2">
            {task.estimated_hours && (
              <span className="flex items-center gap-0.5">
                <IconClock className="h-3 w-3" />
                {task.estimated_hours}h
              </span>
            )}
            {courseName && (
              <span className="flex items-center gap-1">
                <span
                  className="h-2 w-2 rounded-full"
                  style={{
                    backgroundColor: courseColor || "var(--primary)",
                  }}
                />
                {courseName}
              </span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const [view, setView] = useState<ViewMode>("kanban");
  const [search, setSearch] = useState("");
  const { data: allTasks } = useTasks();
  const { data: blocks } = useBlocks();
  const { data: courses } = useCourses();
  const chatStore = useChatStore();
  const user = useAuthStore((s) => s.user);
  const completeMut = useCompleteTask();
  const deleteMut = useDeleteTask();

  const courseMap = new Map(courses?.map((c) => [c.id, c]) || []);

  // Filter tasks by search
  const filteredTasks = (allTasks || []).filter(
    (t) =>
      !search ||
      t.title.toLowerCase().includes(search.toLowerCase()) ||
      t.description?.toLowerCase().includes(search.toLowerCase())
  );

  // Group for kanban
  const grouped = {
    active: filteredTasks.filter((t) => t.status === "active"),
    in_progress: [] as Task[], // future: tasks with blocks today
    completed: filteredTasks.filter((t) => t.status === "completed"),
  };

  // Move tasks with blocks scheduled today into "in_progress"
  const todayStr = new Date().toDateString();
  const todayTaskIds = new Set(
    blocks
      ?.filter((b) => new Date(b.start).toDateString() === todayStr)
      .map((b) => b.task_id) || []
  );
  grouped.in_progress = grouped.active.filter((t) =>
    todayTaskIds.has(t.id)
  );
  grouped.active = grouped.active.filter((t) => !todayTaskIds.has(t.id));

  const todayBlocks =
    blocks?.filter(
      (b) => new Date(b.start).toDateString() === todayStr
    ) || [];

  const studyHours =
    todayBlocks.reduce(
      (sum, b) =>
        sum + (new Date(b.end).getTime() - new Date(b.start).getTime()),
      0
    ) /
    (1000 * 60 * 60);

  return (
    <div className="space-y-6">
      {/* Top bar: Search + icons + profile */}
      <div className="flex items-center gap-4">
        <div className="relative max-w-md w-full">
          <IconSearch className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--muted-foreground)]" />
          <input
            type="text"
            placeholder="Search tasks..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-10 w-full rounded-lg border border-[var(--border)] bg-[var(--background)] pl-10 pr-4 text-sm text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
          />
        </div>
        <div className="ml-auto flex items-center gap-2">
          <button className="flex h-10 w-10 items-center justify-center rounded-lg text-[var(--muted-foreground)] transition-colors hover:bg-[var(--muted)]">
            <IconCalendar className="h-5 w-5" />
          </button>
          <button className="flex h-10 w-10 items-center justify-center rounded-lg text-[var(--muted-foreground)] transition-colors hover:bg-[var(--muted)]">
            <IconHelpCircle className="h-5 w-5" />
          </button>
          <button
            onClick={() => chatStore.open()}
            className="flex h-10 w-10 items-center justify-center rounded-lg text-[var(--muted-foreground)] transition-colors hover:bg-[var(--muted)]"
          >
            <IconChat className="h-5 w-5" />
          </button>
        </div>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--primary)] text-sm font-semibold text-white">
          {user?.display_name?.charAt(0)?.toUpperCase() || "U"}
        </div>
      </div>

      {/* Title section */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[var(--foreground)]">
          Study Planner
        </h1>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            className="border-[var(--primary)] text-[var(--primary)]"
          >
            <IconPlus className="h-4 w-4" />
            Invite
          </Button>
          <Link href="/tasks/new">
            <Button size="sm">
              <IconPlus className="h-4 w-4" />
              New Task
            </Button>
          </Link>
        </div>
      </div>

      {/* Filter bar + view toggles */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button className="flex items-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--muted-foreground)] transition-colors hover:bg-[var(--muted)]">
            <IconFilter className="h-4 w-4" />
            Filter
          </button>
          <button className="flex items-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--muted-foreground)] transition-colors hover:bg-[var(--muted)]">
            <IconCalendar className="h-4 w-4" />
            Today
          </button>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded-lg border border-[var(--border)] p-0.5">
            <button
              onClick={() => setView("kanban")}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                view === "kanban"
                  ? "bg-[var(--primary)] text-white"
                  : "text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
              }`}
            >
              <IconGrid className="inline h-4 w-4 mr-1" />
              Board
            </button>
            <button
              onClick={() => setView("list")}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                view === "list"
                  ? "bg-[var(--primary)] text-white"
                  : "text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
              }`}
            >
              <IconList className="inline h-4 w-4 mr-1" />
              List
            </button>
          </div>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="flex items-center gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[rgba(111,128,255,0.12)]">
              <IconCheckSquare className="h-6 w-6 text-[var(--primary)]" />
            </div>
            <div>
              <p className="text-sm text-[var(--muted-foreground)]">
                Active Tasks
              </p>
              <p className="text-2xl font-bold text-[var(--foreground)]">
                {allTasks?.filter((t) => t.status === "active").length ?? 0}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[rgba(111,128,255,0.08)]">
              <IconClock className="h-6 w-6 text-[var(--primary)]" />
            </div>
            <div>
              <p className="text-sm text-[var(--muted-foreground)]">
                Today&apos;s Blocks
              </p>
              <p className="text-2xl font-bold text-[var(--foreground)]">
                {todayBlocks.length}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[rgba(104,178,102,0.12)]">
              <IconBook className="h-6 w-6 text-[#68b266]" />
            </div>
            <div>
              <p className="text-sm text-[var(--muted-foreground)]">
                Study Hours
              </p>
              <p className="text-2xl font-bold text-[var(--foreground)]">
                {studyHours.toFixed(1)}h
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Kanban / List view */}
      {view === "kanban" ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {kanbanColumns.map((col) => {
            const tasks = grouped[col.key];
            return (
              <div key={col.key} className="space-y-3">
                {/* Column header */}
                <div className="flex items-center gap-2 px-1">
                  <span
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: col.dotColor }}
                  />
                  <span className="text-sm font-semibold text-[var(--foreground)]">
                    {col.label}
                  </span>
                  <span className="ml-auto flex h-5 min-w-[20px] items-center justify-center rounded-full bg-[var(--muted)] px-1.5 text-[10px] font-medium text-[var(--muted-foreground)]">
                    {tasks.length}
                  </span>
                </div>

                {/* Column content */}
                <div className="space-y-2.5 rounded-xl bg-[var(--kanban-column)] p-3 min-h-[200px]">
                  {tasks.length === 0 ? (
                    <p className="py-8 text-center text-xs text-[var(--muted-foreground)]">
                      No tasks
                    </p>
                  ) : (
                    tasks.map((task) => {
                      const course = task.course_id
                        ? courseMap.get(task.course_id)
                        : undefined;
                      return (
                        <KanbanTaskCard
                          key={task.id}
                          task={task}
                          courseName={course?.name}
                          courseColor={course?.color}
                          onComplete={() => completeMut.mutate(task.id)}
                          onDelete={() => deleteMut.mutate(task.id)}
                        />
                      );
                    })
                  )}

                  {/* Add card placeholder */}
                  <Link
                    href="/tasks/new"
                    className="flex items-center justify-center rounded-lg border-2 border-dashed border-[var(--border)] py-3 text-sm text-[var(--muted-foreground)] transition-colors hover:border-[var(--primary)] hover:text-[var(--primary)]"
                  >
                    <IconPlus className="mr-1 h-4 w-4" />
                    Add task
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* List view */
        <div className="space-y-2">
          {filteredTasks.length === 0 ? (
            <Card>
              <CardContent>
                <p className="text-[var(--muted-foreground)] py-4 text-center">
                  No tasks found
                </p>
              </CardContent>
            </Card>
          ) : (
            filteredTasks.map((task) => {
              const course = task.course_id
                ? courseMap.get(task.course_id)
                : undefined;
              return (
                <Card key={task.id} className="group">
                  <CardContent className="flex items-center gap-4">
                    <Badge
                      variant={priorityVariant(task.priority)}
                      className="shrink-0"
                    >
                      {task.priority}
                    </Badge>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-semibold text-[var(--foreground)] truncate">
                        {task.title}
                      </h4>
                      <div className="flex items-center gap-3 text-xs text-[var(--muted-foreground)] mt-0.5">
                        <span>
                          Due{" "}
                          {new Date(task.due_date).toLocaleDateString(
                            undefined,
                            { month: "short", day: "numeric" }
                          )}
                        </span>
                        {task.estimated_hours && (
                          <span>{task.estimated_hours}h est.</span>
                        )}
                      </div>
                    </div>
                    {course && (
                      <div className="flex items-center gap-1.5 shrink-0">
                        <span
                          className="h-2 w-2 rounded-full"
                          style={{
                            backgroundColor: course.color || "var(--primary)",
                          }}
                        />
                        <span className="text-xs text-[var(--muted-foreground)]">
                          {course.name}
                        </span>
                      </div>
                    )}
                    <div className="flex gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                      {task.status === "active" && (
                        <button
                          onClick={() => completeMut.mutate(task.id)}
                          className="rounded p-1.5 text-[var(--muted-foreground)] hover:bg-[var(--muted)] hover:text-[#68b266]"
                        >
                          <IconCheckCircle className="h-4 w-4" />
                        </button>
                      )}
                      <button
                        onClick={() => deleteMut.mutate(task.id)}
                        className="rounded p-1.5 text-[var(--muted-foreground)] hover:bg-[var(--muted)] hover:text-[var(--destructive)]"
                      >
                        <IconTrash className="h-4 w-4" />
                      </button>
                    </div>
                  </CardContent>
                </Card>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
