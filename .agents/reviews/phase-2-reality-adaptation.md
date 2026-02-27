# Phase 2 — Reality Adaptation: Review

## What Was Implemented

### Time Logging
- [x] `app/services/time_log_service.py` — Focus timer (start/stop), manual log entry, list logs, total per task
- [x] `app/schemas/time_log.py` — TimeLogCreate, TimeLogResponse, FocusTimerStart/Stop
- [x] `app/api/time_logs.py` — API routes:
  - POST `/api/time-logs/timer/start` — start focus timer
  - POST `/api/time-logs/timer/stop` — stop focus timer
  - POST `/api/time-logs` — manual time entry
  - GET `/api/time-logs` — list logs (filterable by task)
  - GET `/api/time-logs/total/{task_id}` — total logged time

### Estimation Learning
- [x] `app/services/estimation_learning.py`:
  - `compute_multiplier(session, user_id, course_id, task_type)` — avg(actual/estimated) clamped to [0.5, 3.0]
  - `get_all_multipliers()` — all course+type combos with data
  - `update_course_multiplier()` — persist to Course.estimation_multiplier

### Insights
- [x] `app/services/insights_service.py`:
  - `compute_weekly_insight()` — planned vs actual hours + completion rate
  - `compute_risk_scores()` — per-task deadline risk (0-1 score)
  - `compute_load_curve()` — daily planned hours for next N days
  - `save_weekly_insight()` — persist to Insight table

- [x] `app/api/insights.py` — API routes:
  - GET `/api/insights/weekly` — weekly planned vs actual
  - GET `/api/insights/risk-scores` — task risk ranking
  - GET `/api/insights/load-curve` — 14-day load forecast
  - GET `/api/insights/multipliers` — estimation accuracy data
  - POST `/api/insights/multipliers/refresh/{course_id}` — recalculate

### Frontend
- [x] `/insights` page with: weekly stats cards, risk score list with color-coded badges, bar chart load curve, estimation multiplier table

## What You Must Do Manually

1. **Sleep protection in scheduler** — The sleep hours are checked in `engine.py` slot availability, but the settings page toggle for "protect sleep mode" should be wired to the `sleep_start_hour`/`sleep_end_hour` rules.

2. **Streak-friendly micro blocks** — Not yet implemented in the engine. To add:
   - In `engine.py`, after main allocation, check for tasks with 0 blocks allocated
   - Create minimum 15-min "review" blocks for each to maintain streaks
   - Add a `streak_protection` boolean to SchedulingRules

3. **Multi-calendar conflict policy** — The model supports multiple CalendarBindings per user, but the sync service only reads from `study_calendar_id`. To add multi-calendar:
   - Add a `connected_calendars` JSON field to User (list of calendar IDs + conflict policy)
   - In sync polling, check all connected calendars
   - Feed external events into the scheduler as hard constraints

4. **Celery task for weekly insight generation** — Add a weekly Celery beat task:
   ```python
   "generate-weekly-insights": {
       "task": "app.tasks.insights.generate_all_weekly_insights",
       "schedule": crontab(day_of_week=0, hour=2),  # Sunday 2am
   }
   ```

5. **Frontend focus timer component** — The API endpoints exist but the frontend doesn't have a timer widget. Build a `FocusTimer` component that:
   - Shows a countdown/countup timer
   - Calls `POST /api/time-logs/timer/start` on start
   - Calls `POST /api/time-logs/timer/stop` on stop
   - Displays on the dashboard and calendar block context menu

6. **Charts library** — The insights page uses a basic bar chart with divs. For proper charts, add `recharts` or `chart.js`:
   ```bash
   cd frontend && npm install recharts
   ```
