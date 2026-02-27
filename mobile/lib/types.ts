// Backend model types — mirrors frontend/src/lib/types.ts

export interface User {
  id: number;
  email: string;
  display_name: string;
  avatar_url: string;
  timezone: string;
  study_calendar_id: string | null;
}

export interface Course {
  id: number;
  user_id: number;
  name: string;
  code: string;
  color: string;
  term_start: string | null;
  term_end: string | null;
  estimation_multiplier: number;
  created_at: string;
  updated_at: string;
}

export type TaskStatus = "active" | "completed" | "archived";
export type TaskType = "assignment" | "exam" | "reading" | "project" | "other";
export type Priority = "low" | "medium" | "high" | "critical";
export type FocusLoad = "light" | "medium" | "deep";

export interface Task {
  id: number;
  user_id: number;
  course_id: number | null;
  title: string;
  description: string;
  due_date: string;
  estimated_hours: number | null;
  difficulty: number;
  priority: Priority;
  task_type: TaskType;
  focus_load: FocusLoad;
  status: TaskStatus;
  splittable: boolean;
  min_block_minutes: number;
  max_block_minutes: number;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  tag_ids: number[];
}

export interface TaskCreate {
  title: string;
  due_date: string;
  course_id?: number | null;
  description?: string;
  estimated_hours?: number | null;
  difficulty?: number;
  priority?: Priority;
  task_type?: TaskType;
  focus_load?: FocusLoad;
  splittable?: boolean;
  min_block_minutes?: number;
  max_block_minutes?: number;
  tag_ids?: number[];
}

export interface TaskUpdate {
  title?: string;
  due_date?: string;
  course_id?: number | null;
  description?: string;
  estimated_hours?: number | null;
  difficulty?: number;
  priority?: Priority;
  task_type?: TaskType;
  focus_load?: FocusLoad;
}

export interface StudyBlock {
  id: number;
  user_id: number;
  task_id: number;
  plan_version_id: number | null;
  start: string;
  end: string;
  block_index: number;
  is_pinned: boolean;
  created_at: string;
  task_title: string;
  course_name: string;
  course_color: string;
}

export interface PlanDiffItem {
  action: "added" | "moved" | "deleted";
  block_id: number | null;
  task_title: string;
  old_start: string | null;
  old_end: string | null;
  new_start: string | null;
  new_end: string | null;
}

export interface PlanDiff {
  added: number;
  moved: number;
  deleted: number;
  items: PlanDiffItem[];
  plan_version_id: number | null;
}

export interface PlanVersion {
  id: number;
  version_number: number;
  trigger: string;
  diff_summary: string;
  created_at: string;
}

export interface Tag {
  id: number;
  user_id: number;
  name: string;
  color: string;
  created_at: string;
}

export interface ChatMessage {
  id: number;
  session_id: number;
  role: "user" | "assistant" | "system";
  content: string;
  tool_calls: ToolCallInfo[];
  created_at: string;
}

export interface ToolCallInfo {
  name: string;
  arguments: Record<string, unknown>;
  result?: Record<string, unknown>;
}

export interface ChatSession {
  id: number;
  title: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AvailabilityGrid {
  monday: boolean[];
  tuesday: boolean[];
  wednesday: boolean[];
  thursday: boolean[];
  friday: boolean[];
  saturday: boolean[];
  sunday: boolean[];
}

export interface SchedulingRules {
  daily_max_hours: number;
  break_after_minutes: number;
  break_duration_minutes: number;
  max_consecutive_same_subject_minutes: number;
  preferred_start_hour: number;
  preferred_end_hour: number;
  slot_duration_minutes: number;
  sleep_start_hour: number;
  sleep_end_hour: number;
  lighter_weekends: boolean;
  weekend_max_hours: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
