# Phase 0 — Foundations: Review

## What Was Implemented

### Infrastructure
- [x] `pyproject.toml` with all dependencies (FastAPI, SQLModel, Anthropic SDK, Google APIs, Celery, etc.)
- [x] `docker-compose.yml` — PostgreSQL 18, Redis 7, Celery worker + beat
- [x] `Dockerfile` for containerized deployment
- [x] `.env.example` with all config variables
- [x] `.gitignore` for Python, Node, Docker, IDE files

### App Skeleton
- [x] `app/main.py` — FastAPI with async lifespan, CORS middleware
- [x] `app/core/config.py` — Pydantic Settings with all env vars
- [x] `app/core/database.py` — Async SQLAlchemy engine + session factory
- [x] `app/core/security.py` — JWT access + refresh token creation/verification
- [x] `app/core/deps.py` — `get_current_user` dependency, `CurrentUser`/`DbSession` type aliases

### Database Models (14 tables)
- [x] User (email, google_id, google tokens, calendar_id, timezone)
- [x] Course (name, code, color, term dates, estimation_multiplier)
- [x] Task + enums (TaskStatus, TaskType, Priority, FocusLoad)
- [x] StudyBlock (task_id, plan_version_id, start/end, is_pinned)
- [x] CalendarBinding (provider, external_event_id, last_synced_hash)
- [x] Tag + TaskTag (M2M join table)
- [x] SharingRule (owner, shared_with, visibility levels)
- [x] TimeLog (timer/manual, start/end, duration)
- [x] Material (file metadata, extraction status, s3_key)
- [x] Insight (planned vs actual hours, risk score per week)
- [x] PlanVersion (version_number, trigger, JSON snapshot, diff_summary)
- [x] AvailabilityGrid (7x96 boolean JSON) + SchedulingRules
- [x] ChatSession + ChatMessage (role, content, tool_calls JSON)

### Alembic
- [x] `alembic.ini` + `alembic/env.py` (sync driver, imports all models)
- [x] `alembic/script.py.mako` template

### Auth
- [x] Google OAuth flow (`/auth/google` → redirect, `/auth/google/callback` → upsert + JWT)
- [x] Token refresh (`/auth/refresh`)
- [x] Logout endpoint
- [x] `/auth/me` returns current user

### Services
- [x] Plan versioning (create_plan_version, rollback_to_version, list_plan_versions)
- [x] Google Calendar creation (create_study_plan_calendar on OAuth callback)

### Infrastructure
- [x] Celery worker config with beat schedule (5-min polling stub)
- [x] Health endpoints (`/health`, `/health/db`)
- [x] Test infrastructure (aiosqlite, async fixtures, dependency overrides)
- [x] 3 passing tests (health, health/db, auth/me)

## What You Must Do Manually

1. **Create `.env` from `.env.example`** — Fill in real values:
   - `SECRET_KEY` — generate a random 32+ char string
   - `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — from Google Cloud Console
   - `ANTHROPIC_API_KEY` — from Anthropic console

2. **Google Cloud Console setup**:
   - Create a project at https://console.cloud.google.com
   - Enable "Google Calendar API"
   - Create OAuth 2.0 credentials (Web Application type)
   - Add `http://localhost:8123/auth/google/callback` to authorized redirect URIs
   - Add `http://localhost:3000` to authorized JavaScript origins

3. **Start services**:
   ```bash
   cp .env.example .env   # then edit with real values
   docker-compose up -d db redis
   uv run alembic upgrade head
   uv run uvicorn app.main:app --reload --port 8123
   ```

4. **Run initial migration** — No migration file generated yet. Run:
   ```bash
   uv run alembic revision --autogenerate -m "initial schema"
   uv run alembic upgrade head
   ```

5. **Python version** — Project uses Python 3.11.4. If you upgrade to 3.12+, update `requires-python` in `pyproject.toml`.
