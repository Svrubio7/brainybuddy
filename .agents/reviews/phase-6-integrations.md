# Phase 6 — Integrations: Review

## What Was Implemented

### LMS Connectors
- [x] `app/services/integrations/base.py` — Abstract `LMSConnector` (authenticate, fetch_assignments, fetch_courses)
- [x] `app/services/integrations/canvas.py` — Canvas REST API connector (Bearer token auth, courses, assignments)
- [x] `app/services/integrations/moodle.py` — Moodle Web Services connector (wstoken auth, courses, assignments)

### Third-Party Sync
- [x] `app/services/integrations/notion_sync.py` — Notion bidirectional sync (push/pull tasks, database pages)
- [x] `app/services/integrations/todoist_sync.py` — Todoist REST API v2 sync (push/pull tasks, priority mapping)

### Holiday Detection
- [x] `app/services/integrations/holiday_detection.py`:
  - `get_holidays(country, year, state)` — public holidays via `holidays` library
  - `detect_reduced_availability()` — compound detection: public holidays, travel days, cluster gaps, academic breaks

### API Routes (`app/api/integrations.py`)
- [x] GET `/api/integrations` — list connected integrations
- [x] POST `/api/integrations/canvas/connect` + `/sync`
- [x] POST `/api/integrations/moodle/connect` + `/sync`
- [x] GET `/api/integrations/holidays`
- [x] GET `/api/integrations/holidays/reduced-availability`

## What You Must Do Manually

1. **Install holidays library**:
   ```bash
   uv add holidays
   ```

2. **Canvas API setup**:
   - Get an API token from Canvas (Account → Settings → New Access Token)
   - Canvas base URL is usually `https://yourschool.instructure.com`
   - Test with: `curl -H "Authorization: Bearer TOKEN" https://BASE/api/v1/courses`

3. **Google Classroom connector** — Not implemented. To add:
   - Use Google Classroom API (OAuth scope: `classroom.courses.readonly`, `classroom.coursework.me`)
   - Similar pattern to Canvas connector
   - Requires additional Google Cloud Console API enablement

4. **Apple Calendar (CalDAV)** — Not implemented. To add:
   - Use `caldav` Python library
   - Apple requires app-specific passwords for CalDAV access
   - Implement as another CalendarBinding provider

5. **Notion setup**:
   - Create a Notion integration at https://developers.notion.com
   - Share a database with the integration
   - Store the integration token and database ID per user

6. **Todoist setup**:
   - Get API token from Todoist Settings → Integrations → Developer
   - Or implement OAuth flow for user-facing auth

7. **Email parser** — Not implemented. To add:
   - Gmail API connector (OAuth scope: `gmail.readonly`)
   - Watch for emails matching patterns ("new assignment", "deadline changed")
   - Use Claude to extract deadline changes from email body
   - Auto-update tasks

8. **Integration management frontend** — No frontend pages. Build:
   - `/integrations` page — list of available integrations with connect/disconnect
   - Setup wizard per integration (Canvas URL + token, Notion database picker, etc.)
   - Sync status + last synced timestamp

9. **Holiday auto-detection** — Wire holidays into the scheduler:
   - On plan generation, check `detect_reduced_availability()` for the planning horizon
   - Reduce available slots on holiday dates by the returned factor
