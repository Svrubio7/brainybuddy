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
  TokenResponse,
  User,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8123";

class ApiClient {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    if (typeof window !== "undefined") {
      this.accessToken = localStorage.getItem("access_token");
      this.refreshToken = localStorage.getItem("refresh_token");
    }
  }

  setTokens(access: string, refresh: string) {
    this.accessToken = access;
    this.refreshToken = refresh;
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", access);
      localStorage.setItem("refresh_token", refresh);
    }
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    }
  }

  private async fetch<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`;
    }

    let response = await fetch(`${API_URL}${path}`, { ...options, headers });

    // Try refresh if 401
    if (response.status === 401 && this.refreshToken) {
      const refreshed = await this.doRefresh();
      if (refreshed) {
        headers["Authorization"] = `Bearer ${this.accessToken}`;
        response = await fetch(`${API_URL}${path}`, { ...options, headers });
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API error: ${response.status}`);
    }

    if (response.status === 204) return undefined as T;
    return response.json();
  }

  private async doRefresh(): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      });
      if (!response.ok) return false;
      const data: TokenResponse = await response.json();
      this.setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      this.clearTokens();
      return false;
    }
  }

  // Auth
  getGoogleAuthUrl = () => this.fetch<{ auth_url: string }>("/auth/google");
  getMe = () => this.fetch<User>("/auth/me");

  // Tasks
  createTask = (data: TaskCreate) =>
    this.fetch<Task>("/api/tasks", { method: "POST", body: JSON.stringify(data) });
  listTasks = (params?: { status?: string; course_id?: number }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.course_id) query.set("course_id", String(params.course_id));
    const qs = query.toString();
    return this.fetch<Task[]>(`/api/tasks${qs ? `?${qs}` : ""}`);
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
