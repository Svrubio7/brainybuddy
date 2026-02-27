import { eq, asc } from "drizzle-orm";
import type { ExpoSQLiteDatabase } from "drizzle-orm/expo-sqlite";
import { api } from "../api";
import type { Task, StudyBlock } from "../types";
import * as schema from "./schema";

const MAX_RETRIES = 5;

type DB = ExpoSQLiteDatabase<typeof schema>;

// ── Push: flush outbox to server ─────────────────────────────────

export async function syncToServer(db: DB): Promise<{
  pushed: number;
  failed: number;
}> {
  const pending = await db
    .select()
    .from(schema.outbox)
    .where(undefined) // all rows
    .orderBy(asc(schema.outbox.id));

  let pushed = 0;
  let failed = 0;

  for (const entry of pending) {
    if (entry.retries >= MAX_RETRIES) {
      failed++;
      continue;
    }

    try {
      const payload = JSON.parse(entry.payload) as Record<string, unknown>;
      await dispatchAction(entry.action, entry.entity_id, payload);

      // Remove from outbox on success
      await db.delete(schema.outbox).where(eq(schema.outbox.id, entry.id));
      pushed++;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Unknown error";
      await db
        .update(schema.outbox)
        .set({
          retries: entry.retries + 1,
          last_error: message,
        })
        .where(eq(schema.outbox.id, entry.id));
      failed++;
    }
  }

  return { pushed, failed };
}

async function dispatchAction(
  action: string,
  entityId: number | null,
  payload: Record<string, unknown>,
): Promise<void> {
  switch (action) {
    case "create_task":
      await api.createTask(payload as Parameters<typeof api.createTask>[0]);
      break;
    case "update_task":
      if (entityId == null) throw new Error("Missing entity_id for update_task");
      await api.updateTask(
        entityId,
        payload as Parameters<typeof api.updateTask>[1],
      );
      break;
    case "delete_task":
      if (entityId == null) throw new Error("Missing entity_id for delete_task");
      await api.deleteTask(entityId);
      break;
    case "complete_task":
      if (entityId == null)
        throw new Error("Missing entity_id for complete_task");
      await api.completeTask(entityId);
      break;
    case "add_time":
      if (entityId == null) throw new Error("Missing entity_id for add_time");
      await api.addTime(entityId, payload.additional_hours as number);
      break;
    case "move_block":
      if (entityId == null) throw new Error("Missing entity_id for move_block");
      await api.moveBlock(
        entityId,
        payload.start as string,
        payload.end as string,
      );
      break;
    case "send_message":
      await api.sendMessage(
        payload.message as string,
        payload.session_id as number | undefined,
      );
      break;
    default:
      throw new Error(`Unknown outbox action: ${action}`);
  }
}

// ── Pull: fetch latest data from server ──────────────────────────

export async function syncFromServer(db: DB): Promise<{
  tasks: number;
  blocks: number;
}> {
  const [remoteTasks, remoteBlocks] = await Promise.all([
    api.listTasks(),
    api.getBlocks(),
  ]);

  const now = new Date().toISOString();

  // Upsert tasks
  for (const task of remoteTasks) {
    const existing = await db
      .select()
      .from(schema.tasks)
      .where(eq(schema.tasks.id, task.id))
      .limit(1);

    if (existing.length > 0 && existing[0].dirty) {
      // Local has unsaved changes — skip (server-wins happens after push)
      continue;
    }

    const row = taskToRow(task, now);
    if (existing.length > 0) {
      await db.update(schema.tasks).set(row).where(eq(schema.tasks.id, task.id));
    } else {
      await db.insert(schema.tasks).values({ ...row, id: task.id });
    }
  }

  // Replace study blocks wholesale (they are server-authoritative)
  await db.delete(schema.studyBlocks);
  for (const block of remoteBlocks) {
    await db.insert(schema.studyBlocks).values(blockToRow(block, now));
  }

  return { tasks: remoteTasks.length, blocks: remoteBlocks.length };
}

// ── Conflict resolution ──────────────────────────────────────────

export interface ConflictPair<T> {
  local: T;
  remote: T;
}

/**
 * Server-wins conflict resolution.
 * Returns the remote version — called after outbox is flushed and
 * server state is canonical.
 */
export function resolveConflict<T>(local: T, remote: T): T {
  // Strategy: server wins. The remote copy is always preferred once
  // we have successfully pushed any local changes via the outbox.
  return remote;
}

// ── Helpers ──────────────────────────────────────────────────────

function taskToRow(task: Task, syncedAt: string) {
  return {
    user_id: task.user_id,
    course_id: task.course_id,
    title: task.title,
    description: task.description,
    due_date: task.due_date,
    estimated_hours: task.estimated_hours,
    difficulty: task.difficulty,
    priority: task.priority,
    task_type: task.task_type,
    focus_load: task.focus_load,
    status: task.status,
    splittable: task.splittable,
    min_block_minutes: task.min_block_minutes,
    max_block_minutes: task.max_block_minutes,
    completed_at: task.completed_at,
    created_at: task.created_at,
    updated_at: task.updated_at,
    synced_at: syncedAt,
    dirty: false,
  } as const;
}

function blockToRow(block: StudyBlock, syncedAt: string) {
  return {
    id: block.id,
    user_id: block.user_id,
    task_id: block.task_id,
    plan_version_id: block.plan_version_id,
    start: block.start,
    end: block.end,
    block_index: block.block_index,
    is_pinned: block.is_pinned,
    created_at: block.created_at,
    task_title: block.task_title,
    course_name: block.course_name,
    course_color: block.course_color,
    synced_at: syncedAt,
    dirty: false,
  } as const;
}
