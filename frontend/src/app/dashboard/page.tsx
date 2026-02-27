"use client";

import Link from "next/link";
import {
  CheckSquare,
  Clock,
  BookOpen,
  Plus,
  MessageSquare,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useTasks, useBlocks, useCourses } from "@/lib/hooks";
import { useChatStore } from "@/lib/stores";
import type { Task } from "@/lib/types";

function priorityVariant(p: string) {
  if (p === "critical") return "critical";
  if (p === "high") return "high";
  if (p === "medium") return "medium";
  return "low";
}

function TaskCard({ task, courseName, courseColor }: { task: Task; courseName?: string; courseColor?: string }) {
  return (
    <Link href="/tasks" className="block">
      <Card className="hover:shadow-md transition-shadow cursor-pointer">
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <Badge variant={priorityVariant(task.priority)}>
              {task.priority}
            </Badge>
            {courseName && (
              <div className="flex items-center gap-1.5">
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: courseColor || "var(--accent)" }}
                />
                <span className="text-xs text-[var(--muted-foreground)]">
                  {courseName}
                </span>
              </div>
            )}
          </div>
          <h4 className="text-base font-semibold text-[var(--foreground)] leading-tight">
            {task.title}
          </h4>
          {task.description && (
            <p className="text-xs text-[var(--muted-foreground)] line-clamp-2">
              {task.description}
            </p>
          )}
          <div className="flex items-center justify-between text-xs text-[var(--muted-foreground)]">
            <span>
              Due {new Date(task.due_date).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
            </span>
            {task.estimated_hours && (
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {task.estimated_hours}h
              </span>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

export default function DashboardPage() {
  const { data: tasks } = useTasks({ status: "active" });
  const { data: blocks } = useBlocks();
  const { data: courses } = useCourses();
  const chatStore = useChatStore();

  const courseMap = new Map(courses?.map((c) => [c.id, c]) || []);
  const upcomingTasks = tasks?.slice(0, 6) || [];
  const todayBlocks =
    blocks?.filter((b) => {
      const blockDate = new Date(b.start).toDateString();
      return blockDate === new Date().toDateString();
    }) || [];

  const studyHours =
    todayBlocks.reduce(
      (sum, b) =>
        sum + (new Date(b.end).getTime() - new Date(b.start).getTime()),
      0
    ) /
    (1000 * 60 * 60);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[var(--foreground)]">
          Dashboard
        </h1>
        <div className="flex gap-2">
          <Link href="/tasks/new">
            <Button size="sm">
              <Plus className="h-4 w-4" />
              New Task
            </Button>
          </Link>
          <Button variant="outline" size="sm" onClick={() => chatStore.open()}>
            <MessageSquare className="h-4 w-4" />
            Chat
          </Button>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="flex items-center gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[rgba(170,120,166,0.12)]">
              <CheckSquare className="h-6 w-6 text-[var(--accent)]" />
            </div>
            <div>
              <p className="text-sm text-[var(--muted-foreground)]">
                Active Tasks
              </p>
              <p className="text-2xl font-bold text-[var(--foreground)]">
                {tasks?.length ?? 0}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[rgba(86,136,224,0.12)]">
              <Clock className="h-6 w-6 text-[#5688e0]" />
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
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[rgba(131,194,157,0.15)]">
              <BookOpen className="h-6 w-6 text-[#68b266]" />
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

      {/* Two-column section */}
      <div className="grid gap-6 lg:grid-cols-5">
        {/* Upcoming tasks - wider */}
        <div className="lg:col-span-3 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-[var(--foreground)]">
              Upcoming Tasks
            </h2>
            <Link
              href="/tasks"
              className="text-sm text-[var(--accent)] hover:underline"
            >
              View all
            </Link>
          </div>
          {upcomingTasks.length === 0 ? (
            <Card>
              <CardContent>
                <p className="text-[var(--muted-foreground)] py-4 text-center">
                  No active tasks. Create one to get started!
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              {upcomingTasks.map((task) => {
                const course = task.course_id
                  ? courseMap.get(task.course_id)
                  : undefined;
                return (
                  <TaskCard
                    key={task.id}
                    task={task}
                    courseName={course?.name}
                    courseColor={course?.color}
                  />
                );
              })}
            </div>
          )}
        </div>

        {/* Today's schedule - narrower */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-[var(--foreground)]">
              Today&apos;s Schedule
            </h2>
            <Link
              href="/calendar"
              className="text-sm text-[var(--accent)] hover:underline"
            >
              Calendar
            </Link>
          </div>
          <Card>
            <CardContent>
              {todayBlocks.length === 0 ? (
                <p className="text-[var(--muted-foreground)] py-4 text-center">
                  No blocks scheduled today
                </p>
              ) : (
                <div className="space-y-3">
                  {todayBlocks.map((block) => (
                    <div
                      key={block.id}
                      className="flex items-center gap-3 rounded-lg border border-[var(--border)] p-3"
                    >
                      <span
                        className="h-full w-1 self-stretch rounded-full"
                        style={{
                          backgroundColor:
                            block.course_color || "var(--accent)",
                        }}
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-[var(--foreground)] truncate">
                          {block.task_title}
                        </p>
                        <p className="text-xs text-[var(--muted-foreground)]">
                          {block.course_name}
                        </p>
                      </div>
                      <p className="shrink-0 text-xs font-medium text-[var(--muted-foreground)]">
                        {new Date(block.start).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                        {" - "}
                        {new Date(block.end).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
