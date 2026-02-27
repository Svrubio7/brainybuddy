# Phase 1F — MVP Frontend: Review

## What Was Implemented

### Scaffold
- [x] Next.js 15 + App Router + TypeScript
- [x] Tailwind CSS 4 with CSS custom properties (light + dark mode)
- [x] PostCSS config with `@tailwindcss/postcss`
- [x] Environment config (`.env.local.example`)

### UI Primitives (Radix-based)
- [x] Button (6 variants: default, destructive, outline, secondary, ghost, link)
- [x] Input
- [x] Textarea
- [x] Card (Card, CardHeader, CardTitle, CardContent)
- [x] Badge (4 variants)
- [x] Skeleton (loading placeholder)
- [x] `cn()` utility (clsx + tailwind-merge)

### Auth
- [x] Login page with Google OAuth redirect
- [x] Callback page (`/auth/callback`) — exchanges code for JWT
- [x] JWT storage in localStorage with auto-refresh

### API Layer
- [x] `lib/api.ts` — Full API client class with all endpoints
- [x] Auto token refresh on 401
- [x] Methods for: tasks, courses, tags, schedule, availability, chat, sync

### State Management
- [x] `lib/stores.ts` — Zustand stores: auth, calendar, diff, chat
- [x] `lib/hooks.ts` — TanStack Query hooks for all data fetching/mutations
- [x] `lib/types.ts` — Complete TypeScript types mirroring all backend schemas

### Pages (11 routes, all building successfully)
- [x] `/` — Landing + Google login
- [x] `/auth/callback` — OAuth callback handler
- [x] `/dashboard` — Stats cards, upcoming tasks, today's schedule
- [x] `/tasks` — Task list with filters, complete/delete actions
- [x] `/tasks/new` — Full task creation form (all fields)
- [x] `/calendar` — Week grid (7-day × 15-hour), navigation, replan + confirm
- [x] `/chat` — Chat interface with message bubbles, tool call badges, SSE
- [x] `/settings` — Availability grid (paintable 7x24) + scheduling rules form
- [x] `/insights` — Weekly stats, risk scores, load curve, estimation multipliers
- [x] `/materials` — Drag-and-drop upload, extraction preview, confirm tasks

### Layout
- [x] Sidebar navigation (Dashboard, Calendar, Tasks, Chat, Insights, Materials, Settings)
- [x] Shared layout component per section
- [x] **Frontend builds to 13 static pages with zero errors**

## What You Must Do Manually

1. **Install dependencies**:
   ```bash
   cd frontend && npm install
   ```

2. **Create `.env.local`**:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8123
   NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id
   ```

3. **@dnd-kit drag-and-drop** — The calendar currently renders blocks as positioned divs. To enable drag-and-drop:
   - Import `DndContext`, `useDraggable`, `useDroppable` from `@dnd-kit/core`
   - Wrap the calendar grid in `DndContext`
   - Make each `StudyBlock` draggable
   - Make each time slot droppable
   - On drop, call `api.moveBlock(blockId, newStart, newEnd)`

4. **Month view and Agenda view** — Only week view is implemented. Add:
   - `MonthView.tsx` — standard month grid with block dots
   - `AgendaView.tsx` — linear list of upcoming blocks
   - View switcher in calendar header

5. **CommandPalette (Cmd+K)** — The `cmdk` package is installed but the component isn't built. Implement with:
   - Quick task creation
   - Navigation shortcuts
   - Search tasks/courses

6. **Responsive mobile nav** — Sidebar is hidden on mobile (`hidden md:flex`). Add a hamburger menu or bottom tab nav for mobile web.

7. **Toast notifications** — Radix Toast is installed but not wired up. Add a `Toaster` component for success/error feedback on mutations.

8. **Real-time SSE** — The `/api/chat/stream` endpoint exists but the frontend chat uses the non-streaming endpoint. To enable streaming:
   - Use `fetch()` with `ReadableStream` to read SSE chunks
   - Parse each `data:` line as JSON
   - Render text incrementally
