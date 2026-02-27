# Phase 7 — Mobile (React Native / Expo): Review

## What Was Implemented

### Scaffold
- [x] `mobile/package.json` — Expo project with all dependencies
- [x] `mobile/app.json` — Expo config (name, slug, icons, plugins)
- [x] `mobile/tsconfig.json` — TypeScript config extending Expo base

### Navigation
- [x] `mobile/app/_layout.tsx` — Root layout with SafeAreaProvider
- [x] `mobile/app/(tabs)/_layout.tsx` — Tab navigator: Home, Calendar, Tasks, Chat, Profile

### Screens
- [x] **Home** (`index.tsx`) — Greeting, stats row, current block with progress bar, upcoming blocks, due-soon tasks, pull-to-refresh
- [x] **Calendar** (`calendar.tsx`) — Week strip with day selection, vertical day timeline (60px/hour), positioned study blocks, "now" indicator, auto-scroll to current hour
- [x] **Tasks** (`tasks.tsx`) — Filter tabs, overdue/upcoming grouping, priority dots, complete/add-time actions with haptics
- [x] **Chat** (`chat.tsx`) — Message bubbles, tool call chips, suggestion buttons, keyboard-avoiding input
- [x] **Profile** (`profile.tsx`) — Avatar, settings sections (schedule, sync, preferences, account), Google Calendar status, logout

### Data Layer
- [x] `mobile/lib/api.ts` — API client using AsyncStorage for tokens (same endpoints as web)
- [x] `mobile/lib/types.ts` — Full TypeScript types (mirror of web)
- [x] `mobile/lib/db/schema.ts` — Drizzle ORM SQLite schema (tasks, blocks, courses, outbox)
- [x] `mobile/lib/db/sync.ts` — Offline sync engine (syncToServer, syncFromServer, server-wins conflict resolution)

### Components
- [x] `mobile/components/FocusTimer.tsx` — Pomodoro timer with configurable durations, progress ring, session counter, haptic feedback, vibration alerts

## What You Must Do Manually

1. **Install dependencies**:
   ```bash
   cd mobile && npm install
   ```

2. **Expo development**:
   ```bash
   npx expo start
   # Scan QR code with Expo Go app on your phone
   ```

3. **AsyncStorage** — The API client uses `@react-native-async-storage/async-storage`. Make sure it's installed and linked:
   ```bash
   npx expo install @react-native-async-storage/async-storage
   ```

4. **SQLite setup** — expo-sqlite requires Expo SDK 50+. Verify with:
   ```bash
   npx expo install expo-sqlite
   ```
   Then initialize the database on app startup.

5. **Drizzle migrations** — The schema is defined but needs initialization:
   - Create a `mobile/lib/db/index.ts` that opens the SQLite database
   - Run `drizzle.push()` on app startup to create tables

6. **Push notifications**:
   - Configure `expo-notifications` with push token registration
   - Backend needs an endpoint to store push tokens
   - Trigger notifications for: upcoming study block, missed block, deadline approaching

7. **Home widget** — Not implemented. Requires:
   - iOS: `expo-widgets` or native WidgetKit module
   - Android: `expo-widgets` or native AppWidget
   - Shows current/next study block with countdown

8. **Gamification** — Not implemented. To add:
   - Streak tracking (consecutive days with completed blocks)
   - XP system (points per completed block/task)
   - Achievements model + UI (badge collection)
   - All opt-in via user preferences

9. **Weekly review** — Not implemented. Build:
   - Screen showing planned vs actual for the week
   - Auto-suggestions for next week
   - "Plan next week" button that triggers replan

10. **Accessibility**:
    - OpenDyslexic font toggle: download font, add to `app.json` fonts config
    - ADHD mode: reduced UI clutter, larger touch targets, simplified navigation
    - Screen reader labels on all interactive elements

11. **Offline mode** — The outbox sync pattern is implemented but not wired to the UI:
    - Wrap API calls to write to local DB first, then outbox
    - Show sync status indicator in the header
    - Auto-sync when connectivity returns (use `@react-native-community/netinfo`)
