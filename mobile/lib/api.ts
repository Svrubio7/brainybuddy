import AsyncStorage from "@react-native-async-storage/async-storage";
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

const API_URL = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8123";

const TOKEN_KEY = "brainybuddy_access_token";
const REFRESH_KEY = "brainybuddy_refresh_token";

class ApiClient {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private initialized = false;

  /** Load persisted tokens from AsyncStorage. Call once at app startup. */
  async init(): Promise<void> {
    if (this.initialized) return;
    const [access, refresh] = await Promise.all([
      AsyncStorage.getItem(TOKEN_KEY),
      AsyncStorage.getItem(REFRESH_KEY),
    ]);
    this.accessToken = access;
    this.refreshToken = refresh;
    this.initialized = true;
  }

  async setTokens(access: string, refresh: string): Promise<void> {
    this.accessToken = access;
    this.refreshToken = refresh;
    await Promise.all([
      AsyncStorage.setItem(TOKEN_KEY, access),
      AsyncStorage.setItem(REFRESH_KEY, refresh),
    ]);
  }

  async clearTokens(): Promise<void> {
    this.accessToken = null;
    this.refreshToken = null;
    await Promise.all([
      AsyncStorage.removeItem(TOKEN_KEY),
      AsyncStorage.removeItem(REFRESH_KEY),
    ]);
  }

  get isAuthenticated(): boolean {
    return this.accessToken !== null;
  }

  // ── Core fetch with auto-refresh ──────────────────────────────

  private async request<T>(
    path: string,
    options: RequestInit = {},
  ): Promise<T> {
    await this.init();

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`;
    }

    let response = await fetch(`${API_URL}${path}`, { ...options, headers });

    // Try token refresh on 401
    if (response.status === 401 && this.refreshToken) {
      const refreshed = await this.doRefresh();
      if (refreshed) {
        headers["Authorization"] = `Bearer ${this.accessToken}`;
        response = await fetch(`${API_URL}${path}`, { ...options, headers });
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(
        (error as { detail?: string }).detail ||
          `API error: ${response.status}`,
      );
    }

    if (response.status === 204) return undefined as T;
    return response.json() as Promise<T>;
  }

  private async doRefresh(): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      });
      if (!response.ok) return false;
      const data = (await response.json()) as TokenResponse;
      await this.setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      await this.clearTokens();
      return false;
    }
  }

  // ── Auth ───────────────────────────────────────────────────────

  getGoogleAuthUrl = () =>
    this.request<{ auth_url: string }>("/auth/google");

  getMe = () => this.request<User>("/auth/me");

  // ── Tasks ──────────────────────────────────────────────────────

  createTask = (data: TaskCreate) =>
    this.request<Task>("/api/tasks", {
      method: "POST",
      body: JSON.stringify(data),
    });

  listTasks = (params?: { status?: string; course_id?: number }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.course_id) query.set("course_id", String(params.course_id));
    const qs = query.toString();
    return this.request<Task[]>(`/api/tasks${qs ? `?${qs}` : ""}`);
  };

  getTask = (id: number) => this.request<Task>(`/api/tasks/${id}`);

  updateTask = (id: number, data: TaskUpdate) =>
    this.request<Task>(`/api/tasks/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });

  deleteTask = (id: number) =>
    this.request<void>(`/api/tasks/${id}`, { method: "DELETE" });

  completeTask = (id: number) =>
    this.request<Task>(`/api/tasks/${id}/complete`, { method: "POST" });

  addTime = (id: number, hours: number) =>
    this.request<Task>(`/api/tasks/${id}/add-time`, {
      method: "POST",
      body: JSON.stringify({ additional_hours: hours }),
    });

  // ── Courses ────────────────────────────────────────────────────

  createCourse = (data: Partial<Course>) =>
    this.request<Course>("/api/courses", {
      method: "POST",
      body: JSON.stringify(data),
    });

  listCourses = () => this.request<Course[]>("/api/courses");

  updateCourse = (id: number, data: Partial<Course>) =>
    this.request<Course>(`/api/courses/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });

  deleteCourse = (id: number) =>
    this.request<void>(`/api/courses/${id}`, { method: "DELETE" });

  // ── Tags ───────────────────────────────────────────────────────

  createTag = (data: { name: string; color?: string }) =>
    this.request<Tag>("/api/tags", {
      method: "POST",
      body: JSON.stringify(data),
    });

  listTags = () => this.request<Tag[]>("/api/tags");

  deleteTag = (id: number) =>
    this.request<void>(`/api/tags/${id}`, { method: "DELETE" });

  // ── Schedule ───────────────────────────────────────────────────

  generatePlan = (reason = "manual_replan") =>
    this.request<PlanDiff>("/api/schedule/generate", {
      method: "POST",
      body: JSON.stringify({ reason }),
    });

  confirmPlan = () =>
    this.request<{ message: string; plan_version_id: number }>(
      "/api/schedule/confirm",
      { method: "POST" },
    );

  getBlocks = (start?: string, end?: string) => {
    const query = new URLSearchParams();
    if (start) query.set("start", start);
    if (end) query.set("end", end);
    const qs = query.toString();
    return this.request<StudyBlock[]>(
      `/api/schedule/blocks${qs ? `?${qs}` : ""}`,
    );
  };

  moveBlock = (id: number, start: string, end: string) =>
    this.request<StudyBlock>(`/api/schedule/blocks/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ start, end }),
    });

  getVersions = () => this.request<PlanVersion[]>("/api/schedule/versions");

  rollback = (versionId: number) =>
    this.request<{ message: string }>(
      `/api/schedule/rollback/${versionId}`,
      { method: "POST" },
    );

  // ── Availability ───────────────────────────────────────────────

  getAvailability = () =>
    this.request<AvailabilityGrid>("/api/availability");

  updateAvailability = (data: AvailabilityGrid) =>
    this.request<AvailabilityGrid>("/api/availability", {
      method: "PUT",
      body: JSON.stringify(data),
    });

  getRules = () => this.request<SchedulingRules>("/api/rules");

  updateRules = (data: SchedulingRules) =>
    this.request<SchedulingRules>("/api/rules", {
      method: "PUT",
      body: JSON.stringify(data),
    });

  // ── Chat ───────────────────────────────────────────────────────

  sendMessage = (message: string, sessionId?: number) =>
    this.request<ChatMessage>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message, session_id: sessionId }),
    });

  getChatHistory = (sessionId: number) =>
    this.request<ChatMessage[]>(
      `/api/chat/history?session_id=${sessionId}`,
    );

  // ── Sync ───────────────────────────────────────────────────────

  getSyncStatus = () =>
    this.request<{ google_connected: boolean; calendar_id: string | null }>(
      "/api/sync/status",
    );

  triggerSync = () =>
    this.request<{ status: string }>("/api/sync/trigger", {
      method: "POST",
    });
}

export const api = new ApiClient();
