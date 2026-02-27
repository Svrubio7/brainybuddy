# Phase 1 — MVP Backend: Review

## What Was Implemented

### Pydantic Schemas (`app/schemas/`)
- [x] `task.py` — TaskCreate, TaskUpdate, TaskResponse, AddTimeRequest
- [x] `course.py` — CourseCreate, CourseUpdate, CourseResponse
- [x] `tag.py` — TagCreate, TagUpdate, TagResponse
- [x] `availability.py` — AvailabilityGridSchema (7x96 booleans), SchedulingRulesSchema
- [x] `schedule.py` — StudyBlockResponse, MoveBlockRequest, PlanDiffItem/Response, PlanVersionResponse
- [x] `chat.py` — ChatRequest, ChatMessageResponse, ToolCallInfo, ChatSessionResponse

### CRUD Services + API Routes
- [x] Task CRUD — create, list (filterable), get, update, delete, complete, add_time
- [x] Course CRUD — create, list, get, update, delete
- [x] Tag CRUD — create, list, get, update, delete
- [x] All routes at `/api/tasks`, `/api/courses`, `/api/tags`

### Availability
- [x] GET/PUT `/api/availability` — 7-day × 96-slot boolean grid
- [x] GET/PUT `/api/rules` — scheduling rules (daily cap, breaks, sleep, weekends)

### Scheduling Engine v1 (`app/services/scheduler/engine.py`)
- [x] 15-minute slot allocation
- [x] Earliest-deadline-first with priority ordering
- [x] Difficulty buffer multiplier (1 + (difficulty-3)*0.1)
- [x] Hard constraints: availability grid, no overlap, daily cap, sleep protection
- [x] Soft constraints: break cadence, max consecutive same subject, weekend limits
- [x] Minimum-viable-progress blocks when overloaded
- [x] Full regeneration (not incremental)

### Plan Diff (`app/services/scheduler/diff.py`)
- [x] Computes added/moved/deleted blocks between old and new plans

### Schedule API
- [x] POST `/api/schedule/generate` — generate + preview diff
- [x] POST `/api/schedule/confirm` — persist new plan
- [x] GET `/api/schedule/blocks` — get blocks (date range filter)
- [x] PATCH `/api/schedule/blocks/{id}` — move/resize block (pins it)
- [x] GET `/api/schedule/versions` — list plan versions
- [x] POST `/api/schedule/rollback/{id}` — rollback to version

### Google Calendar Sync (`app/services/sync/google_calendar.py`)
- [x] Push block to Google (with brainybuddy_block_id in extendedProperties)
- [x] Update/delete Google events
- [x] Pull changes from Google (incremental sync token support)
- [x] Event hash computation for change detection
- [x] Celery task stubs for periodic polling

### LLM Chat v1
- [x] 6 tool schemas (create_task, update_task, set_constraint, trigger_replan, mark_done, cant_study_today)
- [x] Chat service with Anthropic SDK (Claude Sonnet 4)
- [x] System prompt with task context injection
- [x] POST `/api/chat` — send message, get response + tool calls
- [x] POST `/api/chat/stream` — SSE streaming endpoint
- [x] GET `/api/chat/history` — chat history by session
- [x] GET `/api/chat/sessions` — list sessions

### Sync API
- [x] POST `/api/sync/google/connect|disconnect`
- [x] POST `/api/sync/trigger` — manual sync
- [x] GET `/api/sync/status`

### Tests
- [x] 5 task CRUD tests
- [x] 5 scheduler engine tests
- [x] 1 course CRUD test
- [x] **Total: 14 passing tests**

## What You Must Do Manually

1. **Tool call execution** — The chat service extracts tool calls from Claude but does NOT execute them automatically. You need to implement tool execution logic that:
   - Takes each `tool_call` from the response
   - Calls the corresponding service function (e.g., `task_service.create_task`)
   - Returns results to the user for confirmation before destructive actions

2. **Preview cache** — The `_preview_cache` in `app/api/schedule.py` is an in-memory dict. For production, replace with Redis:
   ```python
   # In schedule.py, replace _preview_cache with:
   # redis.set(f"plan_preview:{user.id}", json.dumps(blocks), ex=600)
   ```

3. **Google Calendar polling** — The Celery beat task `poll_google_calendar_changes` is a stub. To implement:
   - Query all users with `study_calendar_id`
   - Call `pull_changes_from_google` per user
   - Compare hashes, update CalendarBindings
   - Trigger replan on detected changes

4. **Webhook vs polling** — For production, replace 5-min polling with Google Calendar push notifications (webhooks). Requires a public HTTPS endpoint.

5. **Rate limiting** — Add Redis-based rate limiting for Google Calendar API calls (quota: 1M queries/day, but per-user limits apply).
