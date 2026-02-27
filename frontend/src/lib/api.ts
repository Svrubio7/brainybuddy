import type {
  AvailabilityGrid,
  ChatMessage,
  Course,
  PlanDiff,
  PlanVersion,
  SchedulingRules,
  StudyBlock,
  Tag,
  Task,
  TaskCreate,
  TaskUpdate,
  User,
} from "./types";
import { supabase } from "./supabase";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8123";

class ApiClient {
  private async getAccessToken(): Promise<string | null> {
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
  }

  private async fetch<T>(path: string, options: RequestInit = {}): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30_000);

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    const token = await this.getAccessToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers,
        signal: controller.signal,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `API error: ${response.status}`);
      }

      if (response.status === 204) return undefined as T;
      return response.json();
    } finally {
      clearTimeout(timeoutId);
    }
  }

  // Auth
  provision = async () => {
    const token = await this.getAccessToken();
    if (!token) throw new Error("No session");
    return this.fetch<User>("/auth/provision", {
      method: "POST",
      body: JSON.stringify({ access_token: token }),
    });
  };
  getMe = () => this.fetch<User>("/auth/me");

  // Tasks
  createTask = (data: TaskCreate) =>
    this.fetch<Task>("/api/tasks", { method: "POST", body: JSON.stringify(data) });
  listTasks = async (params?: { status?: string; course_id?: number }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.course_id) query.set("course_id", String(params.course_id));
    query.set("limit", "200");
    const qs = query.toString();
    const res = await this.fetch<{ items: Task[]; total: number }>(`/api/tasks?${qs}`);
    return res.items;
  };
  getTask = (id: number) => this.fetch<Task>(`/api/tasks/${id}`);
  updateTask = (id: number, data: TaskUpdate) =>
    this.fetch<Task>(`/api/tasks/${id}`, { method: "PATCH", body: JSON.stringify(data) });
  deleteTask = (id: number) =>
    this.fetch<void>(`/api/tasks/${id}`, { method: "DELETE" });
  completeTask = (id: number) =>
    this.fetch<Task>(`/api/tasks/${id}/complete`, { method: "POST" });
  addTime = (id: number, hours: number) =>
    this.fetch<Task>(`/api/tasks/${id}/add-time`, {
      method: "POST",
      body: JSON.stringify({ additional_hours: hours }),
    });

  // Courses
  createCourse = (data: Partial<Course>) =>
    this.fetch<Course>("/api/courses", { method: "POST", body: JSON.stringify(data) });
  listCourses = () => this.fetch<Course[]>("/api/courses");
  updateCourse = (id: number, data: Partial<Course>) =>
    this.fetch<Course>(`/api/courses/${id}`, { method: "PATCH", body: JSON.stringify(data) });
  deleteCourse = (id: number) =>
    this.fetch<void>(`/api/courses/${id}`, { method: "DELETE" });

  // Tags
  createTag = (data: { name: string; color?: string }) =>
    this.fetch<Tag>("/api/tags", { method: "POST", body: JSON.stringify(data) });
  listTags = () => this.fetch<Tag[]>("/api/tags");
  deleteTag = (id: number) =>
    this.fetch<void>(`/api/tags/${id}`, { method: "DELETE" });

  // Schedule
  generatePlan = (reason = "manual_replan") =>
    this.fetch<PlanDiff>("/api/schedule/generate", {
      method: "POST",
      body: JSON.stringify({ reason }),
    });
  confirmPlan = () =>
    this.fetch<{ message: string; plan_version_id: number }>("/api/schedule/confirm", {
      method: "POST",
    });
  getBlocks = (start?: string, end?: string) => {
    const query = new URLSearchParams();
    if (start) query.set("start", start);
    if (end) query.set("end", end);
    const qs = query.toString();
    return this.fetch<StudyBlock[]>(`/api/schedule/blocks${qs ? `?${qs}` : ""}`);
  };
  moveBlock = (id: number, start: string, end: string) =>
    this.fetch<StudyBlock>(`/api/schedule/blocks/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ start, end }),
    });
  getVersions = () => this.fetch<PlanVersion[]>("/api/schedule/versions");
  rollback = (versionId: number) =>
    this.fetch<{ message: string }>(`/api/schedule/rollback/${versionId}`, {
      method: "POST",
    });

  // Availability
  getAvailability = () => this.fetch<AvailabilityGrid>("/api/availability");
  updateAvailability = (data: AvailabilityGrid) =>
    this.fetch<AvailabilityGrid>("/api/availability", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  getRules = () => this.fetch<SchedulingRules>("/api/rules");
  updateRules = (data: SchedulingRules) =>
    this.fetch<SchedulingRules>("/api/rules", {
      method: "PUT",
      body: JSON.stringify(data),
    });

  // Chat
  sendMessage = (message: string, sessionId?: number) =>
    this.fetch<ChatMessage>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message, session_id: sessionId }),
    });
  getChatHistory = (sessionId: number) =>
    this.fetch<ChatMessage[]>(`/api/chat/history?session_id=${sessionId}`);

  // Sync
  getSyncStatus = () => this.fetch<{ google_connected: boolean; calendar_id: string | null }>("/api/sync/status");
  triggerSync = () => this.fetch<{ status: string }>("/api/sync/trigger", { method: "POST" });
}

export const api = new ApiClient();
