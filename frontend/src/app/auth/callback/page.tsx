"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/stores";

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const code = searchParams.get("code");
    if (!code) {
      router.push("/");
      return;
    }

    // The backend handles the code exchange via /auth/google/callback
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8123";
    fetch(`${API_URL}/auth/google/callback?code=${encodeURIComponent(code)}`)
      .then((res) => res.json())
      .then((data) => {
        api.setTokens(data.access_token, data.refresh_token);
        return api.getMe();
      })
      .then((user) => {
        useAuthStore.getState().setUser(user);
        router.push("/dashboard");
      })
      .catch(() => {
        router.push("/");
      });
  }, [router, searchParams]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <p className="text-lg">Signing in...</p>
    </div>
  );
}

export default function AuthCallback() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center">Loading...</div>}>
      <CallbackContent />
    </Suspense>
  );
}
