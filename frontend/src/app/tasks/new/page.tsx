"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCreateTask } from "@/lib/hooks";
import type { Priority, TaskType, FocusLoad } from "@/lib/types";

export default function NewTaskPage() {
  const router = useRouter();
  const createTask = useCreateTask();

  const [title, setTitle] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [estimatedHours, setEstimatedHours] = useState("");
  const [difficulty, setDifficulty] = useState("3");
  const [priority, setPriority] = useState<Priority>("medium");
  const [taskType, setTaskType] = useState<TaskType>("assignment");
  const [focusLoad, setFocusLoad] = useState<FocusLoad>("medium");
  const [description, setDescription] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createTask.mutateAsync({
      title,
      due_date: new Date(dueDate).toISOString(),
      estimated_hours: estimatedHours ? parseFloat(estimatedHours) : undefined,
      difficulty: parseInt(difficulty),
      priority,
      task_type: taskType,
      focus_load: focusLoad,
      description,
    });
    router.push("/tasks");
  };

  return (
    <div className="max-w-2xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>New Task</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Title *</label>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} required />
            </div>

            <div>
              <label className="text-sm font-medium">Due Date *</label>
              <Input type="datetime-local" value={dueDate} onChange={(e) => setDueDate(e.target.value)} required />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Estimated Hours</label>
                <Input type="number" step="0.5" value={estimatedHours} onChange={(e) => setEstimatedHours(e.target.value)} />
              </div>
              <div>
                <label className="text-sm font-medium">Difficulty (1-5)</label>
                <Input type="number" min="1" max="5" value={difficulty} onChange={(e) => setDifficulty(e.target.value)} />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium">Priority</label>
                <select className="flex h-10 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm" value={priority} onChange={(e) => setPriority(e.target.value as Priority)}>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">Type</label>
                <select className="flex h-10 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm" value={taskType} onChange={(e) => setTaskType(e.target.value as TaskType)}>
                  <option value="assignment">Assignment</option>
                  <option value="exam">Exam</option>
                  <option value="reading">Reading</option>
                  <option value="project">Project</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">Focus Load</label>
                <select className="flex h-10 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm" value={focusLoad} onChange={(e) => setFocusLoad(e.target.value as FocusLoad)}>
                  <option value="light">Light</option>
                  <option value="medium">Medium</option>
                  <option value="deep">Deep</option>
                </select>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium">Description</label>
              <Textarea value={description} onChange={(e) => setDescription(e.target.value)} />
            </div>

            <div className="flex gap-2">
              <Button type="submit" disabled={createTask.isPending}>
                {createTask.isPending ? "Creating..." : "Create Task"}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.back()}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
