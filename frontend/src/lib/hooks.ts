"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./api";
import type { TaskCreate, TaskUpdate } from "./types";

// Tasks
export function useTasks(params?: { status?: string; course_id?: number }) {
  return useQuery({
    queryKey: ["tasks", params],
    queryFn: () => api.listTasks(params),
  });
}

export function useTask(id: number) {
  return useQuery({
    queryKey: ["tasks", id],
    queryFn: () => api.getTask(id),
    enabled: id > 0,
  });
}

export function useCreateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TaskCreate) => api.createTask(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function useUpdateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: TaskUpdate }) => api.updateTask(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function useDeleteTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.deleteTask(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function useCompleteTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.completeTask(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

// Courses
export function useCourses() {
  return useQuery({ queryKey: ["courses"], queryFn: api.listCourses });
}

// Tags
export function useTags() {
  return useQuery({ queryKey: ["tags"], queryFn: api.listTags });
}

// Schedule
export function useBlocks(start?: string, end?: string) {
  return useQuery({
    queryKey: ["blocks", start, end],
    queryFn: () => api.getBlocks(start, end),
  });
}

export function useGeneratePlan() {
  return useMutation({ mutationFn: (reason?: string) => api.generatePlan(reason) });
}

export function useConfirmPlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.confirmPlan(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["blocks"] }),
  });
}

export function useMoveBlock() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, start, end }: { id: number; start: string; end: string }) =>
      api.moveBlock(id, start, end),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["blocks"] }),
  });
}

export function usePlanVersions() {
  return useQuery({ queryKey: ["plan-versions"], queryFn: api.getVersions });
}

export function useRollback() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (versionId: number) => api.rollback(versionId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["blocks"] }),
  });
}

// Availability
export function useAvailability() {
  return useQuery({ queryKey: ["availability"], queryFn: api.getAvailability });
}

export function useRules() {
  return useQuery({ queryKey: ["rules"], queryFn: api.getRules });
}

// Chat
export function useSendMessage() {
  return useMutation({
    mutationFn: ({ message, sessionId }: { message: string; sessionId?: number }) =>
      api.sendMessage(message, sessionId),
  });
}

export function useChatHistory(sessionId: number | null) {
  return useQuery({
    queryKey: ["chat-history", sessionId],
    queryFn: () => api.getChatHistory(sessionId!),
    enabled: !!sessionId,
  });
}
