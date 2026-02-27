"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    if (token) {
      router.push("/dashboard");
    }
  }, [router]);

  const handleLogin = async () => {
    try {
      const { auth_url } = await api.getGoogleAuthUrl();
      window.location.href = auth_url;
    } catch {
      // Fallback for development without Google OAuth
      router.push("/dashboard");
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 p-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-2">BrainyBuddy</h1>
        <p className="text-lg text-[var(--muted-foreground)]">
          AI-powered study planner that runs your semester
        </p>
      </div>

      <div className="flex flex-col gap-4 w-full max-w-sm">
        <Button size="lg" onClick={handleLogin} className="w-full">
          Sign in with Google
        </Button>
        <p className="text-xs text-center text-[var(--muted-foreground)]">
          We need Google access to sync your study plan with Google Calendar
        </p>
      </div>
    </main>
  );
}
