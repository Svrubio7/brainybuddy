"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTasks, useBlocks } from "@/lib/hooks";
import { useChatStore } from "@/lib/stores";

export default function DashboardPage() {
  const { data: tasks } = useTasks({ status: "active" });
  const { data: blocks } = useBlocks();
  const chatStore = useChatStore();

  const upcomingTasks = tasks?.slice(0, 5) || [];
  const todayBlocks = blocks?.filter((b) => {
    const blockDate = new Date(b.start).toDateString();
    return blockDate === new Date().toDateString();
  }) || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="flex gap-2">
          <Link href="/tasks/new">
            <Button>New Task</Button>
          </Link>
          <Button variant="outline" onClick={() => chatStore.open()}>
            Chat
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Active Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{tasks?.length ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Today&apos;s Blocks</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{todayBlocks.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Study Hours Today</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {(
                todayBlocks.reduce(
                  (sum, b) => sum + (new Date(b.end).getTime() - new Date(b.start).getTime()),
                  0
                ) /
                (1000 * 60 * 60)
              ).toFixed(1)}
              h
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Upcoming Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            {upcomingTasks.length === 0 ? (
              <p className="text-[var(--muted-foreground)]">No active tasks</p>
            ) : (
              <ul className="space-y-2">
                {upcomingTasks.map((task) => (
                  <li key={task.id} className="flex justify-between items-center">
                    <Link href={`/tasks`} className="hover:underline font-medium">
                      {task.title}
                    </Link>
                    <span className="text-sm text-[var(--muted-foreground)]">
                      {new Date(task.due_date).toLocaleDateString()}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Today&apos;s Schedule</CardTitle>
          </CardHeader>
          <CardContent>
            {todayBlocks.length === 0 ? (
              <p className="text-[var(--muted-foreground)]">No blocks scheduled today</p>
            ) : (
              <ul className="space-y-2">
                {todayBlocks.map((block) => (
                  <li key={block.id} className="flex justify-between items-center">
                    <span className="font-medium">{block.task_title}</span>
                    <span className="text-sm text-[var(--muted-foreground)]">
                      {new Date(block.start).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                      {" - "}
                      {new Date(block.end).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
