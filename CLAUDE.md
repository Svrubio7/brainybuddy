# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BrainyBuddy is an AI-powered study planner for students. It has three core systems: a **deterministic planning engine** (tasks + constraints + calendar → plan), a **sync system** (two-way Google/Apple Calendar mirroring), and an **LLM assistant** (converts user intent into structured actions, tutoring). Scheduling and sync must be consistent and reliable; the LLM layer makes it friendly.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend (web) | Next.js (React) + TypeScript |
| Frontend (mobile) | React Native (Expo) — later phase |
| Backend | FastAPI (Python) + Pydantic v2 |
| Database | PostgreSQL (SQLAlchemy/SQLModel) |
| Migrations | Alembic |
| Cache/Queue | Redis + Celery/RQ |
| Object Storage | S3-compatible |
| Observability | Sentry + OpenTelemetry |
| Package Manager | uv |
| Containerization | Docker Compose |

## Commands

```bash
# Setup
cp .env.example .env
uv sync
docker-compose up -d db

# Migrations
uv run alembic upgrade head

# Dev server
uv run uvicorn app.main:app --reload --port 8123

# Health checks
curl -s http://localhost:8123/health
curl -s http://localhost:8123/health/db

# Swagger UI
# http://localhost:8123/docs

# Cleanup
docker-compose down
```

## Architecture

Monorepo with clean module boundaries (designed to split later):

| Module | Responsibility |
|--------|---------------|
| `scheduler/` | Deterministic planner — 15-min slot allocation, hard/soft constraints |
| `sync/` | Calendar connectors (Google Calendar two-way sync via event metadata) |
| `llm/` | Tool-calling LLM interface — schema validation, action preview |
| `ingestion/` | Document parsing (PDF/image/doc) — syllabus, assignments, slides |
| `collab/` | Sharing + permissions (tag-based, busy-only option) |

### Data Model (core entities)

User, Course, Task, StudyBlock, CalendarBinding, Tag, SharingRule, TimeLog, Material, Insight

CalendarBinding tracks `provider`, `external_event_id`, `last_synced_hash` — this is what makes sync work without conflicts.

### Scheduling Engine

- Time slots: 15-minute increments (configurable)
- Planning horizon: now → max(soonest deadline + 14 days, end of term)
- Hard constraints: availability grid, no overlap, deadline completion, daily cap, API quotas
- Soft constraints (scored penalties): max consecutive subject time, break cadence, energy alternation, sleep protection, weekend lightening
- Replanning triggers: user drag, missed session, new assignment, syllabus import, calendar conflict

## Development Workflow

This project uses custom Claude commands in `.claude/commands/`:

- `/plan-feature <feature>` — Create implementation plan (writes to `.agents/plans/`)
- `/execute <path-to-plan>` — Implement from a plan file
- `/commit` — Stage + atomic commit with conventional tag (feat/fix/docs/etc.)
- `/prime` — Load full project context (structure, docs, recent activity)
- `/create-prd <filename>` — Generate a Product Requirements Document

### Workflow pattern: Plan → Execute → Commit

1. `/plan-feature` creates a context-rich plan so execution succeeds in one pass
2. `/execute` implements the plan task-by-task with validation at each step
3. `/commit` creates a conventional commit

## Build Order (from README)

Phase 0: Auth + schema + audit/undo framework → Phase 1: MVP planning + Google sync + chat → Phase 2: Time logging + estimation learning + insights → Phase 3: Document/syllabus ingestion → Phase 4: Advanced scheduling intelligence → Phase 5: Collaboration → Phase 6: Integrations → Phase 7: Mobile daily driver → Phase 8: Premium tutor tier

## Pricing Tiers

- **Free (€0)**: 15 active tasks, basic scheduling, ICS export, limited Google write-back
- **Standard (€8/mo)**: Unlimited tasks, full sync, advanced scheduling, ingestion, sharing
- **Premium Tutor (€18–25/mo)**: Course-aware AI tutor, flashcards, practice exams, Socratic mode
