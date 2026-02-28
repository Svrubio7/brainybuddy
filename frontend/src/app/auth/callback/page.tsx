"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/stores";

function CallbackHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState("Signing in...");

  useEffect(() => {
    let cancelled = false;

    async function handleAuth() {
      try {
        // PKCE flow: exchange the code for a session
        const code = searchParams.get("code");
        if (code) {
          const { error } = await supabase.auth.exchangeCodeForSession(code);
          if (error) throw error;
        }

        // Now get the session (works for both PKCE and implicit flows)
        const { data, error } = await supabase.auth.getSession();
        if (error) throw error;
        if (!data.session) {
          // No code and no session — wait for onAuthStateChange
          return;
        }

        if (cancelled) return;

        // Session exists — provision user and redirect
        const user = await api.provision();
        useAuthStore.getState().setUser(user);
        router.replace("/dashboard");
      } catch (err) {
        console.error("Auth callback error:", err);
        if (!cancelled) {
          setStatus("Authentication failed. Redirecting...");
          setTimeout(() => router.replace("/"), 2000);
        }
      }
    }

    handleAuth();

    // Fallback: listen for auth state changes (handles implicit/hash flow)
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (event === "SIGNED_IN" && session && !cancelled) {
        try {
          const user = await api.provision();
          useAuthStore.getState().setUser(user);
          router.replace("/dashboard");
        } catch {
          router.replace("/");
        }
      }
    });

    return () => {
      cancelled = true;
      subscription.unsubscribe();
    };
  }, [router, searchParams]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <p className="text-lg">{status}</p>
    </div>
  );
}

export default function AuthCallback() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <p className="text-lg">Signing in...</p>
        </div>
      }
    >
      <CallbackHandler />
    </Suspense>
  );
}
