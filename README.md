# brainybuddy

Product structure (what you’re building)
Three core systems

Planning system (deterministic)

Takes tasks + constraints + calendar conflicts → produces a plan.

Sync system (trustworthy)

Ensures the plan is mirrored to Google/Apple calendars and survives edits.

Assistant system (LLM)

Converts user intent and documents into structured actions + helps explain and tutor.

Reasoning: This separation is what makes the product feel reliable. Scheduling and sync must be consistent; the LLM makes it easy and friendly.

Tech stack (specific)
Frontend
Web (main app)

Next.js (React) + TypeScript

Calendar UI: full-feature calendar component (drag/drop, resizing, agenda/week/month)

State/data: TanStack Query + Zustand (or Redux Toolkit)

Mobile

React Native (Expo recommended)

Use native calendar features later (EventKit on iOS for Apple Calendar)

Reasoning: Web first for speed and power-users. Mobile later becomes a “daily companion” (widgets, quick add, focus mode).

Backend

FastAPI (Python) + Pydantic v2 schemas

Postgres (SQLAlchemy or SQLModel)

Redis (caching, rate limiting, job queue coordination)

Background jobs: Celery/RQ + Redis

Object storage: S3-compatible (uploads: syllabus/assignments/slides)

Observability: Sentry + OpenTelemetry

Core services/modules (in one repo initially)

scheduler/ deterministic planner

sync/ calendar connectors

llm/ tool calling + schema validation

ingestion/ doc parsing + extraction

collab/ sharing + permissions

Reasoning: Monorepo is faster early, but keep boundaries clean so you can split later.

Data model (must support sync + sharing + learning)
Main entities

User

Course

Task (assignment/exam/reading/project)

StudyBlock (scheduled instance)

CalendarBinding (provider, external_event_id, last_synced_hash, etc.)

Tag (course tag, personal tag, share tag)

SharingRule (who can see what; busy-only vs details)

TimeLog (actual time spent; optional timer)

Material (uploaded docs, slides, notes)

Insight (derived stats: multipliers, streaks, risk score)

Reasoning: If you don’t model events and bindings cleanly, calendar sync becomes a nightmare.

Scheduling engine spec (deterministic + explainable)
Time representation

15-minute slots (configurable)

Planning horizon: now → max(soonest deadline + 14 days, end of term)

Constraints
Hard

Availability grid

No overlap with fixed commitments (classes/work/events)

Deadline completion (required hours allocated before due)

Daily max study cap

Provider limits (Google API quotas)

Soft (scored penalties)

Max consecutive subject time

Break cadence (e.g., 10–15 min every 60–90 min)

Alternate high/low focus

Early distribution of work

Protect sleep / avoid late study windows

Keep weekends lighter if desired

Output

Study blocks with:

task/course, block index, focus load, “commute friendly”, location hint, linked material

Replanning triggers

User drags blocks

Missed session / “I can’t study today”

“Need +1h”

New assignment

Syllabus import adds tasks

Calendar conflicts appear

Reasoning: Deterministic + fast replans build trust and make this usable daily.

Full development plan (all features included)
Phase 0 — Foundations (2–3 weeks)
Features

Auth + accounts

Google OAuth (required for calendar)

Email login option later (but Google first)

Create dedicated “Study Plan” calendar

Toggle: write into dedicated calendar vs existing

Core schema + migration framework

Task, StudyBlock, CalendarBinding, Tag, Rules

Audit log + undo framework

Every plan generation creates a “plan version”

One-click rollback

Why: These are trust primitives and reduce support burden.

Phase 1 — MVP planning + Google sync (6–8 weeks)
Core features

Manual task creation (Assignment/Exam/Reading/Project)

fields: title, due date, estimate (or unknown), difficulty, priority, focus load, split rules, description

Availability + rules engine v1

weekly grid

daily cap

break cadence

max continuous per subject

preferred windows

no-study days

Scheduling engine v1

earliest-first allocation

respects constraints

chunk sizing

adds buffers for high difficulty

creates “minimum viable progress blocks” when overloaded (Feature #7 below)

Google Calendar sync v1 (two-way)

writes events with internal IDs in metadata

detects external drag/delete and reconciles

conflict policy: “respect user edits and replan around them”

Web calendar UI

week + agenda views

drag/drop + resize blocks

quick actions: mark done, need more time, can’t study today, replan

Chat interface v1 (LLM intake)

“Add tasks by talking”

“Add constraints by talking”

Tool-calling only → produces validated JSON actions

Preview changes + diff

“Will add 12 blocks, move 3, delete 1”

requires confirmation for destructive changes

Why: This is the smallest version that delivers the “it runs my semester” moment.

Phase 2 — “Reality adaptation” + estimation learning (6–10 weeks)
Features

Time logging

“start focus” timer per block (optional)

manual done time entry

Personalized estimation

multipliers by course + task type + difficulty

“you tend to underestimate writing by 30%”

Insights dashboard

weekly planned vs actual

upcoming load curve

“risk score” (Feature #4)

Multi-calendar conflict policy

connect additional Google calendars

“work calendar blocks are hard conflicts”

Protect sleep mode

never schedule after X

keep consistent bedtime routine (soft constraint)

Streak-friendly micro blocks

tiny daily review blocks to maintain momentum

Why: Scheduling without learning becomes inaccurate quickly.

Phase 3 — Document + syllabus ingestion (8–12 weeks)
Features

Assignment upload + extraction

PDF/image/doc upload

extract due date, requirements, deliverables

propose milestones (outline/draft/revise)

confidence score + edit slider

Syllabus ingestion

parse exam dates, assignment schedule, office hours, weekly topics

review screen before creating tasks

Automatic class schedule import

from timetable PDF

creates recurring lecture/lab events

QR scan + quick add

scan handout to create task

Voice input

“Add a 3-hour lab report due Friday”

Chrome extension

add assignment from LMS webpage or PDF viewer

Why: Intake friction is the #1 killer of student productivity apps.

Phase 4 — Advanced scheduling intelligence (8–12 weeks)

(These were the “Pro” features; they’re now inside your €8 tier.)

Features

Energy profile scheduling

“deep work mornings, review evenings”

Spaced repetition auto-blocks

exam dates → spaced review schedule

Interleaving mode

rotate topics for improved retention

Deadline risk score

capacity vs required hours → warns early

Auto-buffer weeks

pre-midterm/finals buffers

Granular chunking by task type

reading vs coding vs writing patterns

Commute-friendly blocks

audio review / flashcards

Adaptive breaks

break length scales with block length

Exam crunch mode

relax some preferences if exam < N days

What-if planner

simulate “part-time job added” or “reduce hobby time”

Grade weighting priority

user inputs % weight → affects scheduling

Why: This is what makes it feel “smarter than a calendar.”

Phase 5 — Collaboration + sharing (6–10 weeks)
Features

Tag-based sharing

share only “Course: Algorithms”

busy-only sharing option

hide personal tasks

Invite links + permissions

view-only

suggest-times (later upgrade)

shared project tasks with roles

Mutual free time finder

propose group study sessions

Shared project timeline

milestones, dependencies

Accountability buddy nudges

opt-in reminders

Study room mode

co-working timer with a friend

Office hours planner

reminders + suggested times

Tutor/TA share view

show plan/busy-only to mentor

Group kanban for projects

lightweight board tied to calendar blocks

“Same class” templates

shared tag packs + standardized schedule patterns

Why: Collaboration increases stickiness and referrals, but must be privacy-first.

Phase 6 — Integrations expansion (ongoing)
Features

LMS integration (Canvas/Moodle)

import assignments and due dates

Email parsing

detect “new assignment posted” or “deadline changed”

Notion/Todoist sync

Google Classroom integration

Public holidays / travel detection

reduces availability automatically

Why: Removing manual entry creates retention.

Phase 7 — Retention polish + mobile “daily driver” (ongoing)
Features

Home widget

today’s plan

Offline mode

view plan and mark done offline

Gamified progress (optional)

streaks, points (opt-in)

Weekly review report + next week auto-plan

“what worked / what didn’t”

Focus mode

block distracting apps (mobile integrations)

Accessibility modes

dyslexia-friendly, ADHD mode, reduced clutter

Why: These reduce churn and make the product part of daily routine.

Phase 8 — Premium Tutor tier (AI-heavy, safe learning) (ongoing)

(These are not about doing assignments for the student. Frame as tutoring + practice + feedback.)

Features

Upload slides/notes as context

course-aware assistant

Lecture-to-notes pipeline

structured notes from lecture materials

Flashcards generator

spaced repetition integration

Practice exam builder

generates practice questions by topic

Socratic tutor mode

teaches via questions + hints

Rubric-based draft feedback

suggests improvements, citations, structure

Explain at different levels

“like I’m 12 / 20 / expert”

Auto glossary

key terms and definitions

Progress quizzes during review blocks

quick checks tied to scheduled sessions

Why: This tier monetizes learning help and supports higher LLM costs.

Pricing (updated: Plus + Pro merged)
Free — €0

Goal: fast “aha” moment without high API cost.

Manual task entry (cap: e.g., 15 active tasks)

Basic availability + basic scheduling

Web calendar view

Preview plan (diff view)

Export ICS

Limited Google write-back (example: 30 events/month)

Basic tags (local only)

Standard — €8/month (or €79/year)

Includes everything from MVP + all “Pro” scheduling intelligence + collaboration basics

Unlimited tasks + unlimited scheduling

Full two-way Google Calendar sync

Replanning tools (missed day, +time)

Advanced scheduling intelligence (energy, spaced repetition, interleaving, risk score, crunch mode, what-if)

Syllabus ingestion + assignment upload extraction (moderate monthly quota)

Multi-calendar policies

Tag-based sharing + busy-only

Mutual free time finder + group study scheduling (basic)

Weekly review report

Mobile app access (RN) when ready

Premium Tutor — €18–€25/month (or €179/year)

(Price depends on your LLM costs/limits; keep it simple and put clear quotas.)

Everything in Standard

Course materials context (slides/lectures/notes)

Notes + flashcards + practice exams + quizzes

Socratic tutor + explanations + draft feedback

Higher context limits and/or better model access

Higher document ingestion limits

Priority processing

Optional group plan — €24–€35/month for 4–6 users

Standard features for all

Enhanced group project tools + admin controls

Build order recommendation (so you don’t drown)

Even though the plan includes everything, build in this order:

Phase 1 + trust layer (preview/undo/audit)

Phase 2 learning + insights (makes planning noticeably better)

Phase 3 ingestion (big retention lift)

Phase 4 advanced scheduling (justifies €8)

Phase 5 collaboration (viral growth)

Phase 8 tutor (high margin if done well)