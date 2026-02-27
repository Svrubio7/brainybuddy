import { create } from "zustand";
import type { PlanDiff, User } from "./types";
import { supabase } from "./supabase";
import { api } from "./api";

interface AuthStore {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setUser: (user: User | null) => void;
  initialize: () => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  initialize: async () => {
    try {
      const { data } = await supabase.auth.getSession();
      if (data.session) {
        const user = await api.getMe();
        set({ user, isAuthenticated: true, isLoading: false });
      } else {
        set({ user: null, isAuthenticated: false, isLoading: false });
      }
    } catch {
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },
  logout: async () => {
    await supabase.auth.signOut();
    set({ user: null, isAuthenticated: false });
  },
}));

interface CalendarStore {
  view: "week" | "month" | "agenda";
  currentDate: Date;
  setView: (view: "week" | "month" | "agenda") => void;
  setCurrentDate: (date: Date) => void;
  nextWeek: () => void;
  prevWeek: () => void;
  today: () => void;
}

export const useCalendarStore = create<CalendarStore>((set) => ({
  view: "week",
  currentDate: new Date(),
  setView: (view) => set({ view }),
  setCurrentDate: (date) => set({ currentDate: date }),
  nextWeek: () =>
    set((s) => ({
      currentDate: new Date(s.currentDate.getTime() + 7 * 24 * 60 * 60 * 1000),
    })),
  prevWeek: () =>
    set((s) => ({
      currentDate: new Date(s.currentDate.getTime() - 7 * 24 * 60 * 60 * 1000),
    })),
  today: () => set({ currentDate: new Date() }),
}));

interface DiffStore {
  diff: PlanDiff | null;
  isOpen: boolean;
  setDiff: (diff: PlanDiff | null) => void;
  open: () => void;
  close: () => void;
}

export const useDiffStore = create<DiffStore>((set) => ({
  diff: null,
  isOpen: false,
  setDiff: (diff) => set({ diff, isOpen: !!diff }),
  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false, diff: null }),
}));

interface ChatStore {
  sessionId: number | null;
  isOpen: boolean;
  setSessionId: (id: number | null) => void;
  toggle: () => void;
  open: () => void;
  close: () => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  sessionId: null,
  isOpen: false,
  setSessionId: (id) => set({ sessionId: id }),
  toggle: () => set((s) => ({ isOpen: !s.isOpen })),
  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false }),
}));
