# Phase 4 — Advanced Scheduling Intelligence: Review

## What Was Implemented

### Energy Profiles (`app/services/scheduler/energy.py`)
- [x] `EnergyProfileType` enum: MORNING_PERSON, NIGHT_OWL, BALANCED
- [x] `EnergyProfile` model with 24 hourly scores (0.0-1.0)
- [x] 3 default presets generated via bell-curve math
- [x] `score_slot_for_task(hour, focus_load, profile)` — deep-focus heavily penalized at low-energy hours
- [x] API: GET/PUT `/api/energy-profile`, GET `/api/energy-profile/presets`

### Spaced Repetition (`app/services/scheduler/spaced_repetition.py`)
- [x] Full SM-2 algorithm implementation
- [x] `compute_next_review(quality, repetitions, easiness, interval)` — returns updated params
- [x] `generate_review_blocks(task_id, exam_date, start_date)` — projects review dates
- [x] Cram session added day before exam if schedule doesn't cover it

### What-If Simulator (`app/services/scheduler/what_if.py`)
- [x] `ScenarioType` enum: ADD_COMMITMENT, REMOVE_HOURS, ADD_TASK, CHANGE_DEADLINE
- [x] `simulate_scenario(session, user_id, scenario)` — runs hypothetical plan without persisting
- [x] Returns diff + warnings
- [x] API: POST `/api/what-if/simulate`

## What You Must Do Manually

1. **Integrate energy scoring into the main scheduler** — `engine.py` currently doesn't use energy scores. To integrate:
   - Load user's energy profile in `generate_plan()`
   - After finding an available slot, call `score_slot_for_task()`
   - Use score as a penalty/preference weight when choosing between candidate slots
   - Sort candidate slots by energy score before allocation

2. **Spaced repetition block generation** — The SM-2 algorithm is implemented but not wired into the scheduler. To add:
   - When a task has `task_type == "exam"`, auto-generate review blocks
   - Call `generate_review_blocks()` and inject review blocks into the plan
   - Add review block tracking (separate from regular study blocks)

3. **What-if frontend** — The API exists but there's no frontend page. Build:
   - `/what-if` page with scenario builder
   - Side-by-side calendar comparison (current plan vs simulated)
   - "Apply this scenario" button that executes the changes

4. **Energy profile editor** — Frontend page needed:
   - 24-hour draggable curve (SVG or canvas)
   - Preset buttons (morning/night/balanced)
   - Save to backend

5. **Exam crunch mode** — Not yet implemented. To add:
   - Detect tasks with `task_type == "exam"` and due date < N days
   - Temporarily relax soft constraints (weekend limits, break cadence)
   - Add a flag `crunch_mode_active` to the schedule response

6. **Grade weighting** — Add a `grade_weight` field (0-100%) to Task model:
   - Higher weight = higher scheduling priority
   - Multiply priority score by grade_weight in task sorting

7. **Interleaving mode** — Not yet implemented. To add:
   - After allocating blocks, check for consecutive same-subject blocks
   - Swap block order to alternate subjects for improved retention
   - Make it a toggle in SchedulingRules
