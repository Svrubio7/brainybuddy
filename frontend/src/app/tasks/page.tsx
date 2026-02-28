"use client";

import Link from "next/link";
import {
  IconPlus,
  IconClock,
  IconGrid,
  IconList,
  IconCheckCircle,
  IconTrash,
} from "@/components/ui/icons";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  useTasks,
  useCompleteTask,
  useDeleteTask,
  useCourses,
} from "@/lib/hooks";
import type { Task } from "@/lib/types";

type ViewMode = "kanban" | "list";

function priorityVariant(p: string) {
  if (p === "critical") return "critical" as const;
  if (p === "high") return "high" as const;
  if (p === "medium") return "medium" as const;
  return "low" as const;
}

const columns = [
  { key: "active", label: "Active", dotColor: "#5688e0" },
  { key: "completed", label: "Completed", dotColor: "#68b266" },
  { key: "archived", label: "Archived", dotColor: "#8b8d9e" },
] as const;

function KanbanCard({
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
                className="rounded p-1 text-[var(--muted-foreground)] hover:bg-[var(--secondary)] hover:text-[#68b266]"
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
              className="rounded p-1 text-[var(--muted-foreground)] hover:bg-[var(--secondary)] hover:text-[var(--destructive)]"
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
                    backgroundColor: courseColor || "var(--accent)",
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

function ListRow({
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
    <Card className="group">
      <CardContent className="flex items-center gap-4">
        <Badge variant={priorityVariant(task.priority)} className="shrink-0">
          {task.priority}
        </Badge>

        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-[var(--foreground)] truncate">
            {task.title}
          </h4>
          <div className="flex items-center gap-3 text-xs text-[var(--muted-foreground)] mt-0.5">
            <span>
              Due{" "}
              {new Date(task.due_date).toLocaleDateString(undefined, {
                month: "short",
                day: "numeric",
              })}
            </span>
            {task.estimated_hours && <span>{task.estimated_hours}h est.</span>}
            <Badge variant="outline" className="text-[10px] px-1.5 py-0">
              {task.task_type}
            </Badge>
          </div>
        </div>

        {courseName && (
          <div className="flex items-center gap-1.5 shrink-0">
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: courseColor || "var(--accent)" }}
            />
            <span className="text-xs text-[var(--muted-foreground)]">
              {courseName}
            </span>
          </div>
        )}

        <div className="flex gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
          {task.status === "active" && (
            <Button size="sm" variant="ghost" onClick={onComplete}>
              <IconCheckCircle className="h-4 w-4 text-[#68b266]" />
            </Button>
          )}
          <Button size="sm" variant="ghost" onClick={onDelete}>
            <IconTrash className="h-4 w-4 text-[var(--destructive)]" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default function TasksPage() {
  const [view, setView] = useState<ViewMode>("kanban");
  const { data: allTasks, isLoading } = useTasks();
  const { data: courses } = useCourses();
  const completeMut = useCompleteTask();
  const deleteMut = useDeleteTask();

  const courseMap = new Map(courses?.map((c) => [c.id, c]) || []);

  const grouped = {
    active: allTasks?.filter((t) => t.status === "active") || [],
    completed: allTasks?.filter((t) => t.status === "completed") || [],
    archived: allTasks?.filter((t) => t.status === "archived") || [],
  };

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[var(--foreground)]">Tasks</h1>
        <div className="flex items-center gap-2">
          {/* View toggle */}
          <div className="flex rounded-lg border border-[var(--border)] p-0.5">
            <button
              onClick={() => setView("kanban")}
              className={`rounded-md p-1.5 transition-colors ${
                view === "kanban"
                  ? "bg-[var(--primary)] text-white"
                  : "text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
              }`}
              title="Kanban"
            >
              <IconGrid className="h-4 w-4" />
            </button>
            <button
              onClick={() => setView("list")}
              className={`rounded-md p-1.5 transition-colors ${
                view === "list"
                  ? "bg-[var(--primary)] text-white"
                  : "text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
              }`}
              title="List"
            >
              <IconList className="h-4 w-4" />
            </button>
          </div>

          <Link href="/tasks/new">
            <Button size="sm">
              <IconPlus className="h-4 w-4" />
              New Task
            </Button>
          </Link>
        </div>
      </div>

      {isLoading ? (
        <p className="text-[var(--muted-foreground)]">Loading...</p>
      ) : view === "kanban" ? (
        /* Kanban view */
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {columns.map((col) => (
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
                <span className="ml-auto flex h-5 min-w-[20px] items-center justify-center rounded-full bg-[var(--secondary)] px-1.5 text-[10px] font-medium text-[var(--muted-foreground)]">
                  {grouped[col.key].length}
                </span>
              </div>

              {/* Column content */}
              <div className="space-y-2.5 rounded-xl bg-[var(--kanban-column)] p-3 min-h-[200px]">
                {grouped[col.key].length === 0 ? (
                  <p className="py-8 text-center text-xs text-[var(--muted-foreground)]">
                    No tasks
                  </p>
                ) : (
                  grouped[col.key].map((task) => {
                    const course = task.course_id
                      ? courseMap.get(task.course_id)
                      : undefined;
                    return (
                      <KanbanCard
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
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* List view */
        <div className="space-y-2">
          {!allTasks?.length ? (
            <p className="text-[var(--muted-foreground)] py-8 text-center">
              No tasks found
            </p>
          ) : (
            allTasks.map((task) => {
              const course = task.course_id
                ? courseMap.get(task.course_id)
                : undefined;
              return (
                <ListRow
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
        </div>
      )}
    </div>
  );
}
