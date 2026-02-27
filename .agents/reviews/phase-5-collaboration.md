# Phase 5 — Collaboration: Review

## What Was Implemented

### Sharing Rules (`app/services/collab/sharing.py`)
- [x] Create sharing rule (by email or user_id, prevents self-sharing)
- [x] List rules I created / shared with me
- [x] View shared schedule respecting visibility:
  - BUSY_ONLY: times only, no details
  - DETAILS: + task title and course name
  - FULL: + task description
- [x] Soft-delete (deactivate) rules
- [x] Pydantic schemas: SharingRuleCreate, SharingRuleResponse, SharedBlockResponse

### Study Groups (`app/services/collab/study_groups.py`)
- [x] `StudyGroup` + `StudyGroupMember` SQLModel tables
- [x] Create group (owner auto-added as member)
- [x] Add/remove members (by email, with permission checks)
- [x] List groups for user (with member counts)
- [x] Find mutual free time (delegates to free_time service)

### Free Time Finder (`app/services/collab/free_time.py`)
- [x] `find_mutual_free_slots(user_ids, session)` — intersects availability grids
- [x] Respects sleep protection per user
- [x] Finds contiguous free runs >= configurable minimum duration
- [x] Returns day + time ranges

### API Routes (`app/api/collab.py`)
- [x] POST `/api/sharing` — create rule
- [x] GET `/api/sharing` — my rules
- [x] GET `/api/sharing/shared-with-me`
- [x] GET `/api/sharing/{id}/schedule` — view shared schedule
- [x] DELETE `/api/sharing/{id}`
- [x] POST `/api/groups` — create group
- [x] GET `/api/groups` — list groups
- [x] POST `/api/groups/{id}/members` — add member
- [x] GET `/api/groups/{id}/free-time`

## What You Must Do Manually

1. **Alembic migration for new tables** — StudyGroup and StudyGroupMember are defined but need a migration:
   ```bash
   uv run alembic revision --autogenerate -m "add study groups"
   uv run alembic upgrade head
   ```

2. **Frontend collaboration pages** — No frontend pages exist. Build:
   - `/sharing` — manage sharing rules, invite by email, view shared-with-me
   - `/groups` — create/manage study groups, member list, free time Venn diagram
   - Share dialog component (reusable modal for tag-based sharing)

3. **Study rooms (WebSocket)** — Not implemented. Requires:
   - WebSocket endpoint for real-time co-working timer
   - `app/api/study_rooms.py` with WebSocket connection manager
   - Frontend: room join/leave, shared timer, participant list, mini-chat

4. **Accountability buddy** — Not implemented. To add:
   - Buddy pairing model (User ↔ User)
   - Notification triggers: missed study block, streak broken, deadline approaching
   - Push notification or email integration

5. **Invite links** — Current sharing uses direct email. Add:
   - Generate unique invite tokens
   - GET `/api/invite/{token}` — accept invite, create sharing rule
   - Configurable expiry

6. **Tag-based sharing filter** — The `tag_filter` field on SharingRule is stored as JSON string but not enforced in `get_shared_schedule()`. Implement:
   - Parse tag_filter as list of tag IDs
   - Filter returned blocks to only include tasks with matching tags

7. **Group project Kanban** — Not implemented. Consider adding:
   - Project model (belongs to group)
   - Kanban columns: todo/in-progress/done
   - Task assignment within groups
