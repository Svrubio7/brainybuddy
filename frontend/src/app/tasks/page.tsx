"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { useTasks, useCompleteTask, useDeleteTask } from "@/lib/hooks";
import { useState } from "react";

const priorityColors: Record<string, string> = {
  critical: "bg-red-500 text-white",
  high: "bg-orange-500 text-white",
  medium: "bg-blue-500 text-white",
  low: "bg-gray-400 text-white",
};

export default function TasksPage() {
  const [filter, setFilter] = useState<string | undefined>(undefined);
  const { data: tasks, isLoading } = useTasks(filter ? { status: filter } : undefined);
  const completeMut = useCompleteTask();
  const deleteMut = useDeleteTask();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Tasks</h1>
        <Link href="/tasks/new">
          <Button>New Task</Button>
        </Link>
      </div>

      <div className="flex gap-2">
        {[undefined, "active", "completed"].map((f) => (
          <Button
            key={f ?? "all"}
            variant={filter === f ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(f)}
          >
            {f === undefined ? "All" : f.charAt(0).toUpperCase() + f.slice(1)}
          </Button>
        ))}
      </div>

      {isLoading ? (
        <p>Loading...</p>
      ) : !tasks?.length ? (
        <p className="text-[var(--muted-foreground)]">No tasks found</p>
      ) : (
        <div className="space-y-3">
          {tasks.map((task) => (
            <Card key={task.id} className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-medium">{task.title}</h3>
                  <Badge className={priorityColors[task.priority]}>{task.priority}</Badge>
                  <Badge variant="outline">{task.task_type}</Badge>
                </div>
                <p className="text-sm text-[var(--muted-foreground)] mt-1">
                  Due: {new Date(task.due_date).toLocaleDateString()} |{" "}
                  Est: {task.estimated_hours ?? "?"}h | Difficulty: {task.difficulty}/5
                </p>
              </div>
              <div className="flex gap-2">
                {task.status === "active" && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => completeMut.mutate(task.id)}
                  >
                    Done
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => deleteMut.mutate(task.id)}
                >
                  Delete
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
