"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/stores";

export default function AuthCallback() {
  const router = useRouter();

  useEffect(() => {
    supabase.auth
      .getSession()
      .then(({ data }) => {
        if (!data.session) throw new Error("No session");
        return api.provision();
      })
      .then((user) => {
        useAuthStore.getState().setUser(user);
        router.push("/dashboard");
      })
      .catch(() => {
        router.push("/");
      });
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <p className="text-lg">Signing in...</p>
    </div>
  );
}
