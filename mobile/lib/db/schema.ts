import { integer, real, text, sqliteTable } from "drizzle-orm/sqlite-core";

/**
 * Local SQLite schema for offline-first storage.
 * Mirrors the server models but adds sync metadata columns.
 */

// ── Tasks ────────────────────────────────────────────────────────

export const tasks = sqliteTable("tasks", {
  id: integer("id").primaryKey(),
  user_id: integer("user_id").notNull(),
  course_id: integer("course_id"),
  title: text("title").notNull(),
  description: text("description").notNull().default(""),
  due_date: text("due_date").notNull(),
  estimated_hours: real("estimated_hours"),
  difficulty: integer("difficulty").notNull().default(3),
  priority: text("priority", {
    enum: ["low", "medium", "high", "critical"],
  })
    .notNull()
    .default("medium"),
  task_type: text("task_type", {
    enum: ["assignment", "exam", "reading", "project", "other"],
  })
    .notNull()
    .default("other"),
  focus_load: text("focus_load", {
    enum: ["light", "medium", "deep"],
  })
    .notNull()
    .default("medium"),
  status: text("status", {
    enum: ["active", "completed", "archived"],
  })
    .notNull()
    .default("active"),
  splittable: integer("splittable", { mode: "boolean" }).notNull().default(true),
  min_block_minutes: integer("min_block_minutes").notNull().default(15),
  max_block_minutes: integer("max_block_minutes").notNull().default(120),
  completed_at: text("completed_at"),
  created_at: text("created_at").notNull(),
  updated_at: text("updated_at").notNull(),

  // Sync metadata
  synced_at: text("synced_at"),
  dirty: integer("dirty", { mode: "boolean" }).notNull().default(false),
});

// ── Study Blocks ─────────────────────────────────────────────────

export const studyBlocks = sqliteTable("study_blocks", {
  id: integer("id").primaryKey(),
  user_id: integer("user_id").notNull(),
  task_id: integer("task_id").notNull(),
  plan_version_id: integer("plan_version_id"),
  start: text("start").notNull(),
  end: text("end").notNull(),
  block_index: integer("block_index").notNull().default(0),
  is_pinned: integer("is_pinned", { mode: "boolean" }).notNull().default(false),
  created_at: text("created_at").notNull(),
  task_title: text("task_title").notNull().default(""),
  course_name: text("course_name").notNull().default(""),
  course_color: text("course_color").notNull().default("#6366F1"),

  // Sync metadata
  synced_at: text("synced_at"),
  dirty: integer("dirty", { mode: "boolean" }).notNull().default(false),
});

// ── Courses (cached) ─────────────────────────────────────────────

export const courses = sqliteTable("courses", {
  id: integer("id").primaryKey(),
  user_id: integer("user_id").notNull(),
  name: text("name").notNull(),
  code: text("code").notNull().default(""),
  color: text("color").notNull().default("#6366F1"),
  term_start: text("term_start"),
  term_end: text("term_end"),
  estimation_multiplier: real("estimation_multiplier").notNull().default(1.0),
  created_at: text("created_at").notNull(),
  updated_at: text("updated_at").notNull(),

  // Sync metadata
  synced_at: text("synced_at"),
});

// ── Outbox (pending mutations to push to server) ─────────────────

export type OutboxAction =
  | "create_task"
  | "update_task"
  | "delete_task"
  | "complete_task"
  | "add_time"
  | "move_block"
  | "send_message";

export const outbox = sqliteTable("outbox", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  action: text("action").notNull(), // OutboxAction
  entity_type: text("entity_type").notNull(), // "task" | "block" | "chat"
  entity_id: integer("entity_id"),
  payload: text("payload").notNull(), // JSON string of the mutation body
  created_at: text("created_at").notNull(),
  retries: integer("retries").notNull().default(0),
  last_error: text("last_error"),
});
