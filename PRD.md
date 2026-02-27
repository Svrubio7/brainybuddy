# BrainyBuddy — Product Requirements Document

## 1. Executive Summary

BrainyBuddy is an AI-powered study planner that transforms how students manage their academic workload. It combines a deterministic scheduling engine with two-way calendar sync and a conversational LLM assistant to produce reliable, adaptive study plans that students can trust daily.

The core value proposition is simple: **"It runs my semester."** Students add tasks (manually or via document upload), set their constraints, and BrainyBuddy produces an optimized study plan synced to their calendar — replanning instantly when life happens.

**MVP Goal**: Deliver a working study planner with manual task entry, constraint-aware scheduling, two-way Google Calendar sync, a drag-and-drop web calendar, and a chat interface for natural-language task intake — enough to replace a student's manual planning workflow entirely.

---

## 2. Mission

**Mission Statement**: Make academic time management effortless, reliable, and intelligent — so students spend time studying, not planning.

**Core Principles**:

1. **Deterministic scheduling builds trust** — the planner must be fast, explainable, and consistent. No black-box AI scheduling.
2. **Sync is sacred** — calendar sync must survive edits, respect user changes, and never lose data.
3. **LLM makes it friendly, not fragile** — the assistant converts intent to structured actions; it never controls scheduling logic directly.
4. **Friction kills adoption** — every interaction (adding tasks, importing syllabi, adjusting plans) must feel effortless.
5. **Privacy-first collaboration** — sharing features default to minimal disclosure (busy-only) and require explicit opt-in.

---

## 3. Target Users

### Primary Persona: University Student (18–25)

- Juggles 4–6 courses, assignments, exams, and personal commitments
- Currently uses Google Calendar + manual planning (or nothing)
- Moderate technical comfort — uses apps daily but won't tolerate setup friction
- Pain points: underestimates time, forgets deadlines, can't replan when things shift, overwhelmed during exam periods

### Secondary Persona: Graduate/Professional Student

- Heavier workload, more self-directed study
- Needs research/writing task support alongside coursework
- Values time tracking and estimation accuracy

### Tertiary Persona: Study Group Coordinator

- Wants to find mutual free time, share project timelines
- Needs visibility into group members' availability without exposing personal details

---

## 4. MVP Scope

### ✅ In Scope (Phase 0 + Phase 1)

**Core Functionality**:
- ✅ Manual task creation (Assignment/Exam/Reading/Project) with title, due date, estimate, difficulty, priority, focus load, split rules
- ✅ Availability + rules engine (weekly grid, daily cap, break cadence, max continuous per subject, preferred windows, no-study days)
- ✅ Deterministic scheduling engine v1 (earliest-first allocation, constraint-respecting, chunk sizing, difficulty buffers, minimum-viable-progress blocks)
- ✅ Web calendar UI (week + agenda views, drag/drop, resize, quick actions: mark done, need more time, can't study today, replan)
- ✅ Chat interface v1 (add tasks/constraints by talking, tool-calling → validated JSON actions)
- ✅ Preview changes + diff view ("Will add 12 blocks, move 3, delete 1" with confirmation for destructive changes)

**Integration**:
- ✅ Google OAuth (required for calendar access)
- ✅ Google Calendar two-way sync (write events with internal IDs in metadata, detect external drag/delete, reconcile with "respect user edits and replan around them")
- ✅ Dedicated "Study Plan" calendar creation with toggle for dedicated vs existing

**Technical Foundation**:
- ✅ Auth + accounts (Google OAuth first, email login later)
- ✅ Core schema + migration framework (Task, StudyBlock, CalendarBinding, Tag, Rules)
- ✅ Audit log + undo framework (plan versioning, one-click rollback)

### ❌ Out of Scope (deferred)

- ❌ Mobile app (React Native — Phase 7)
- ❌ Apple Calendar sync (Phase 6+)
- ❌ Document/syllabus ingestion (Phase 3)
- ❌ Time logging + estimation learning (Phase 2)
- ❌ Advanced scheduling intelligence (energy profiles, spaced repetition, interleaving — Phase 4)
- ❌ Collaboration + sharing (Phase 5)
- ❌ LMS integration, email parsing, Notion/Todoist sync (Phase 6)
- ❌ AI tutor features (flashcards, practice exams, Socratic mode — Phase 8)
- ❌ Gamification, focus mode, widgets (Phase 7)

---

## 5. User Stories

### Primary Stories (MVP)

1. **As a student**, I want to add my assignments with due dates and time estimates, so that I can see everything I need to do in one place.
   - *Example: "Add Lab Report, due Friday, estimated 3 hours, high difficulty"*

2. **As a student**, I want the app to automatically schedule study blocks around my classes and commitments, so that I don't have to figure out when to study.
   - *Example: System allocates three 1-hour blocks across Tuesday/Wednesday/Thursday mornings, avoiding my 10am lecture.*

3. **As a student**, I want to drag and resize study blocks on the calendar, so that I can adjust the plan when something comes up.
   - *Example: Drag Wednesday's block to Thursday evening; system replans remaining blocks accordingly.*

4. **As a student**, I want my study plan synced to Google Calendar, so that I see it alongside my other events.
   - *Example: Study blocks appear in a dedicated "Study Plan" calendar in Google Calendar. Moving an event in Google Calendar is detected and reconciled.*

5. **As a student**, I want to tell the chat "I can't study today" and have the plan adjust immediately, so that I don't fall behind.
   - *Example: Chat response shows diff: "Moved 2 blocks to tomorrow, extended Thursday session by 30 min. Confirm?"*

6. **As a student**, I want to add tasks by chatting naturally, so that I don't have to fill out forms.
   - *Example: "I have a 5-page essay due next Monday and a quiz on Thursday" → system creates two tasks with extracted metadata and schedules them.*

7. **As a student**, I want to preview what will change before the plan updates, so that I feel in control.
   - *Example: Diff view shows added/moved/deleted blocks with confirmation prompt for destructive changes.*

8. **As a student**, I want to undo a replan if I don't like the result, so that I never feel stuck.
   - *Example: One-click rollback restores previous plan version.*

### Technical Stories

9. **As the system**, CalendarBinding must track `external_event_id` and `last_synced_hash` per event, so that two-way sync detects external changes without data loss.

10. **As the system**, every plan generation must create a versioned snapshot, so that audit logs and rollback are always available.

---

## 6. Core Architecture & Patterns

### High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Next.js Frontend                   │
│  Calendar UI · Chat Interface · Diff Preview · Auth  │
└──────────────────────┬──────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────┐
│                 FastAPI Backend                       │
│                                                      │
│  ┌────────────┐ ┌────────┐ ┌─────┐ ┌───────────┐   │
│  │ scheduler/ │ │ sync/  │ │ llm/│ │ ingestion/│   │
│  │ determin.  │ │ gcal   │ │ tool│ │ (future)  │   │
│  │ planner    │ │ 2-way  │ │ call│ │           │   │
│  └─────┬──────┘ └───┬────┘ └──┬──┘ └───────────┘   │
│        │            │         │                      │
│  ┌─────▼────────────▼─────────▼─────────────────┐   │
│  │        PostgreSQL + Redis + Celery            │   │
│  └───────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

### Key Design Patterns

- **Monorepo with clean module boundaries** — `scheduler/`, `sync/`, `llm/`, `ingestion/`, `collab/` are separate modules in one repo. Keep imports directional so they can split later.
- **Deterministic core, LLM at the edges** — scheduling and sync are never LLM-dependent. The LLM produces structured JSON actions that feed into the deterministic engine.
- **Event sourcing for plans** — every plan generation creates a version. Rollback = restore previous version.
- **Conflict resolution policy** — "respect user edits and replan around them." External calendar changes are treated as hard constraints on replan.

### Directory Structure (target)

```
brainybuddy/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── api/                  # Route handlers
│   ├── models/               # SQLAlchemy/SQLModel entities
│   ├── schemas/              # Pydantic v2 request/response schemas
│   ├── services/             # Business logic layer
│   │   ├── scheduler/        # Deterministic planner
│   │   ├── sync/             # Calendar connectors
│   │   └── llm/              # Tool-calling LLM interface
│   ├── core/                 # Config, security, dependencies
│   └── tasks/                # Celery background jobs
├── alembic/                  # Database migrations
├── tests/
│   ├── unit/
│   └── integration/
├── frontend/                 # Next.js app (future)
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

---

## 7. Features (Detailed Specifications)

### 7.1 Task Management

**Purpose**: CRUD for academic tasks with rich metadata.

**Fields**:
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| title | string | yes | |
| due_date | datetime | yes | |
| estimated_hours | float | no | "unknown" triggers LLM estimation prompt |
| difficulty | enum(1-5) | no | default 3 |
| priority | enum(low/med/high/critical) | no | default medium |
| focus_load | enum(light/medium/deep) | no | default medium |
| split_rules | object | no | min/max block size, splittable boolean |
| course_id | FK | no | |
| description | text | no | |
| tags | list[FK] | no | |

**Operations**: Create, update, delete, list (filterable by course/tag/status/due date), mark complete, "need more time" (+hours).

### 7.2 Scheduling Engine v1

**Purpose**: Allocate study blocks to time slots respecting all constraints.

**Algorithm**: Earliest-deadline-first allocation with constraint satisfaction.

**Input**: Active tasks + availability grid + rules + existing calendar events.

**Output**: List of `StudyBlock` records with: task, start/end, block_index, focus_load, linked_material.

**Key behaviors**:
- Chunk tasks into blocks respecting split_rules (min/max block size)
- Add buffer time proportional to difficulty
- Create "minimum viable progress blocks" when overloaded (ensure every task gets at least some time)
- Replanning is full regeneration from current state (not incremental patching)

### 7.3 Google Calendar Sync

**Purpose**: Two-way sync between BrainyBuddy study blocks and Google Calendar events.

**Write path**: StudyBlock → Google Calendar event with `brainybuddy_id` in extended properties.

**Read path**: Poll/webhook for changes → detect moved/deleted events → update CalendarBinding → trigger replan.

**Conflict policy**: External user edits are treated as intentional. Replan works around them.

**CalendarBinding schema**:
| Field | Purpose |
|-------|---------|
| provider | "google" / "apple" |
| external_event_id | Google Calendar event ID |
| last_synced_hash | Hash of last known state — detects external changes |
| study_block_id | FK to internal StudyBlock |
| last_synced_at | Timestamp |

### 7.4 Chat Interface (LLM)

**Purpose**: Natural language → structured actions via tool calling.

**Approach**: LLM receives user message + available tools → produces JSON tool calls → validated by Pydantic schemas → previewed to user → executed on confirmation.

**Available tools**:
- `create_task(title, due_date, estimated_hours, ...)`
- `update_task(task_id, fields...)`
- `set_constraint(type, params...)`
- `trigger_replan(reason)`
- `mark_done(task_id)`
- `cant_study_today()`

**Safety**: Destructive actions (delete, major replan) always require confirmation via diff preview.

### 7.5 Audit Log + Undo

**Purpose**: Every plan generation creates a versioned snapshot. One-click rollback to any previous version.

**Implementation**: `PlanVersion` table with full serialized plan state. Rollback = restore version + sync to calendar.

---

## 8. Technology Stack

### Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.12+ | Runtime |
| FastAPI | latest | Web framework |
| Pydantic v2 | latest | Schema validation |
| SQLAlchemy/SQLModel | latest | ORM |
| Alembic | latest | Migrations |
| PostgreSQL | 18 | Primary database |
| Redis | latest | Cache, rate limiting, job queue |
| Celery/RQ | latest | Background jobs (sync polling, replan) |
| uv | latest | Package management |

### Frontend (Phase 1)
| Technology | Purpose |
|-----------|---------|
| Next.js + TypeScript | Web application |
| TanStack Query | Server state management |
| Zustand (or Redux Toolkit) | Client state |
| Full-feature calendar component | Drag/drop, resize, agenda/week/month views |

### Infrastructure
| Technology | Purpose |
|-----------|---------|
| Docker Compose | Local development |
| S3-compatible storage | File uploads (syllabus, assignments) |
| Sentry | Error tracking |
| OpenTelemetry | Observability |

### Third-Party Integrations
| Service | Purpose | Phase |
|---------|---------|-------|
| Google OAuth | Authentication + calendar access | 0 |
| Google Calendar API | Two-way event sync | 1 |
| LLM provider (Claude/OpenAI) | Chat assistant tool calling | 1 |
| Canvas/Moodle LMS | Assignment import | 6 |
| Apple EventKit | iOS calendar sync | 6+ |

---

## 9. Security & Configuration

### Authentication
- **Primary**: Google OAuth 2.0 (required — grants calendar API access)
- **Secondary**: Email/password login (later phase, for users who don't use Google Calendar)
- **Session**: JWT tokens with refresh rotation

### Configuration (Environment Variables)
| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `GOOGLE_CLIENT_ID` | OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | OAuth client secret |
| `LLM_API_KEY` | API key for LLM provider |
| `S3_BUCKET` / `S3_ENDPOINT` | Object storage |
| `SENTRY_DSN` | Error tracking |
| `SECRET_KEY` | JWT signing key |

### Security Scope
- **In scope**: OAuth token storage encryption, CSRF protection, rate limiting (Redis), input validation (Pydantic), API quota management (Google Calendar)
- **Out of scope for MVP**: SOC2 compliance, E2E encryption, advanced RBAC (only owner access in MVP)

---

## 10. API Specification (Core Endpoints)

### Auth
| Method | Path | Description |
|--------|------|-------------|
| GET | `/auth/google` | Initiate Google OAuth flow |
| GET | `/auth/google/callback` | OAuth callback |
| POST | `/auth/refresh` | Refresh JWT token |
| POST | `/auth/logout` | Revoke session |

### Tasks
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/tasks` | Create task |
| GET | `/api/tasks` | List tasks (filterable) |
| GET | `/api/tasks/{id}` | Get task detail |
| PATCH | `/api/tasks/{id}` | Update task |
| DELETE | `/api/tasks/{id}` | Delete task |
| POST | `/api/tasks/{id}/complete` | Mark task complete |

### Schedule
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/schedule/generate` | Trigger replan |
| GET | `/api/schedule/blocks` | Get current study blocks (date range) |
| PATCH | `/api/schedule/blocks/{id}` | Move/resize block |
| GET | `/api/schedule/preview` | Preview replan diff |
| POST | `/api/schedule/confirm` | Confirm previewed changes |
| POST | `/api/schedule/rollback/{version}` | Rollback to plan version |
| GET | `/api/schedule/versions` | List plan versions |

### Availability & Rules
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/availability` | Get availability grid |
| PUT | `/api/availability` | Update availability grid |
| GET | `/api/rules` | Get scheduling rules |
| PUT | `/api/rules` | Update scheduling rules |

### Calendar Sync
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/sync/google/connect` | Connect Google Calendar |
| POST | `/api/sync/google/disconnect` | Disconnect |
| POST | `/api/sync/trigger` | Force sync now |
| GET | `/api/sync/status` | Sync health/status |

### Chat
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat` | Send message, receive structured actions |
| GET | `/api/chat/history` | Chat history |

### Health
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | API health |
| GET | `/health/db` | Database health |

---

## 11. Success Criteria

### MVP Success Definition

The MVP is successful when a student can: add their semester's tasks, get an auto-generated study plan, see it in Google Calendar, adjust it via drag/drop or chat, and trust it enough to use it daily for one week.

### Functional Requirements
- ✅ User can sign in via Google OAuth and grant calendar access
- ✅ User can create/edit/delete tasks with full metadata
- ✅ System generates a valid study plan respecting all hard constraints
- ✅ Study blocks appear in Google Calendar within 30 seconds of generation
- ✅ External calendar edits are detected and reconciled within 5 minutes
- ✅ User can drag/drop/resize blocks and system replans around changes
- ✅ Chat can create tasks and trigger replans via natural language
- ✅ All destructive changes show a preview diff before execution
- ✅ User can rollback to any previous plan version

### Quality Indicators
- Replan completes in < 2 seconds for a typical student load (20–40 active tasks)
- Calendar sync has zero data loss (no orphaned events, no missing blocks)
- Chat correctly extracts task metadata ≥ 80% of the time on first attempt

---

## 12. Implementation Phases

### Phase 0 — Foundations (2–3 weeks)

**Goal**: Auth, schema, and trust primitives.

**Deliverables**:
- ✅ Google OAuth login flow
- ✅ Core database schema (User, Course, Task, StudyBlock, CalendarBinding, Tag)
- ✅ Alembic migration framework
- ✅ Audit log + plan versioning table
- ✅ One-click rollback mechanism
- ✅ Dedicated "Study Plan" calendar creation on Google
- ✅ Health endpoints + Docker Compose setup

**Validation**: User can sign in, schema migrates cleanly, health endpoints respond.

### Phase 1 — MVP Planning + Google Sync (6–8 weeks)

**Goal**: The core product loop — add tasks, get a plan, see it in calendar, adjust.

**Deliverables**:
- ✅ Task CRUD with full metadata
- ✅ Availability grid + rules engine
- ✅ Scheduling engine v1 (earliest-first, constraint-respecting)
- ✅ Google Calendar two-way sync with conflict reconciliation
- ✅ Web calendar UI (week + agenda, drag/drop, resize, quick actions)
- ✅ Chat interface v1 (tool-calling, preview, confirmation)
- ✅ Diff preview for all plan changes

**Validation**: End-to-end flow works — create task via chat, see blocks on web calendar and Google Calendar, drag a block, confirm replan, rollback.

### Phase 2 — Reality Adaptation (6–10 weeks)

**Goal**: Plans improve over time based on actual study behavior.

**Deliverables**:
- ✅ Time logging (focus timer + manual entry)
- ✅ Personalized estimation multipliers (by course + task type)
- ✅ Insights dashboard (planned vs actual, load curve, risk score)
- ✅ Multi-calendar conflict policies
- ✅ Sleep protection mode
- ✅ Streak-friendly micro blocks

**Validation**: After 2 weeks of use, estimation accuracy visibly improves.

### Phase 3 — Document Ingestion (8–12 weeks)

**Goal**: Remove intake friction — the #1 killer of student productivity apps.

**Deliverables**:
- ✅ Assignment upload + extraction (PDF/image/doc → due date, requirements, milestones)
- ✅ Syllabus ingestion (exam dates, assignment schedule, weekly topics)
- ✅ Timetable PDF → recurring lecture/lab events
- ✅ Confidence scores + edit sliders for extracted data
- ✅ Voice input ("Add a 3-hour lab report due Friday")

**Validation**: Upload a real syllabus, review extracted tasks, confirm, see scheduled plan.

---

## 13. Future Considerations (Phase 4+)

### Phase 4 — Advanced Scheduling Intelligence
Energy profile scheduling, spaced repetition auto-blocks, interleaving mode, deadline risk scores, exam crunch mode, what-if planner, grade weighting priority.

### Phase 5 — Collaboration
Tag-based sharing (busy-only option), invite links with permissions, mutual free time finder, shared project timelines, accountability buddy nudges, study room co-working timer.

### Phase 6 — Integrations
Canvas/Moodle LMS import, email parsing for deadline changes, Notion/Todoist sync, Google Classroom, public holidays/travel detection.

### Phase 7 — Mobile Daily Driver
React Native (Expo) app, home widget, offline mode, gamified progress (opt-in), weekly review + auto-plan, focus mode, accessibility modes (dyslexia-friendly, ADHD mode).

### Phase 8 — Premium Tutor
Course-aware assistant (upload slides/notes as context), lecture-to-notes pipeline, flashcard generator with spaced repetition, practice exam builder, Socratic tutor mode, rubric-based draft feedback, multi-level explanations, auto glossary, progress quizzes during review blocks.

---

## 14. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Google Calendar API quotas** | Sync failures at scale | Rate limiting via Redis, batch operations, exponential backoff, respect quota headers. Hard constraint in scheduler. |
| **Calendar sync data loss** | Orphaned events or missing blocks destroy trust | CalendarBinding with hash-based change detection, audit log for every sync operation, reconciliation job on startup. |
| **LLM hallucinated actions** | Chat creates wrong tasks or deletes data | All LLM output validated by Pydantic schemas, destructive actions require explicit user confirmation via diff preview. |
| **Scheduling engine performance** | Slow replans frustrate users | 15-min slot granularity bounds complexity. Benchmark with 50+ tasks. Cache availability grid. Replan is stateless (full regen, not incremental). |
| **Student adoption / churn** | Users try it once and leave | Phase 0 trust primitives (preview, undo, audit) reduce anxiety. Phase 3 ingestion removes intake friction. Phase 7 retention polish. |

---

## 15. Appendix

### Pricing Model

| Tier | Price | Key Features |
|------|-------|-------------|
| Free | €0 | 15 active tasks, basic scheduling, ICS export, limited Google write-back (30 events/month) |
| Standard | €8/mo (€79/yr) | Unlimited tasks, full sync, advanced scheduling, ingestion, sharing, mobile |
| Premium Tutor | €18–25/mo (€179/yr) | AI tutor, flashcards, practice exams, Socratic mode, higher context/model access |
| Group | €24–35/mo (4–6 users) | Standard features + group project tools + admin controls |

### Key Dependencies

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Calendar API](https://developers.google.com/calendar/api)
- [Pydantic v2](https://docs.pydantic.dev/latest/)
- [SQLModel](https://sqlmodel.tiangolo.com/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [TanStack Query](https://tanstack.com/query)

### Repository

- **Source**: `brainybuddy/` monorepo
- **Custom Claude Commands**: `.claude/commands/` (plan-feature, execute, commit, prime, create-prd)
- **Plan Files**: `.agents/plans/` (created by `/plan-feature`)
