"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import {
  CheckSquare,
  Calendar,
  BarChart3,
  Brain,
  Zap,
  Shield,
  Clock,
  BookOpen,
  ArrowRight,
  Check,
  Mail,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { supabase } from "@/lib/supabase";
import { useAuthStore } from "@/lib/stores";

/* ── Auth Modal ────────────────────────────────────────────── */

function AuthModal({
  open,
  onClose,
  mode: initialMode,
}: {
  open: boolean;
  onClose: () => void;
  mode: "login" | "signup";
}) {
  const [mode, setMode] = useState(initialMode);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  useEffect(() => {
    setMode(initialMode);
    setError("");
    setMessage("");
  }, [initialMode, open]);

  if (!open) return null;

  const handleEmailAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);
    try {
      if (mode === "signup") {
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: { emailRedirectTo: `${window.location.origin}/auth/callback` },
        });
        if (error) throw error;
        setMessage("Check your email for a confirmation link!");
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (error) throw error;
        router.push("/auth/callback");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = async () => {
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-2xl bg-[var(--card)] p-8 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-2xl font-bold text-[var(--foreground)] mb-1">
          {mode === "login" ? "Welcome back" : "Create your account"}
        </h2>
        <p className="text-sm text-[var(--muted-foreground)] mb-6">
          {mode === "login"
            ? "Sign in to continue to BrainyBuddy"
            : "Start organizing your study life"}
        </p>

        {/* Google button */}
        <button
          onClick={handleGoogle}
          className="flex w-full items-center justify-center gap-3 rounded-lg border border-[var(--border)] bg-[var(--card)] px-4 py-2.5 text-sm font-medium text-[var(--foreground)] transition-colors hover:bg-[var(--secondary)]"
        >
          <svg className="h-5 w-5" viewBox="0 0 24 24">
            <path
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
              fill="#4285F4"
            />
            <path
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              fill="#34A853"
            />
            <path
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              fill="#FBBC05"
            />
            <path
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              fill="#EA4335"
            />
          </svg>
          Continue with Google
        </button>

        <div className="my-5 flex items-center gap-3">
          <div className="h-px flex-1 bg-[var(--border)]" />
          <span className="text-xs text-[var(--muted-foreground)]">or</span>
          <div className="h-px flex-1 bg-[var(--border)]" />
        </div>

        {/* Email form */}
        <form onSubmit={handleEmailAuth} className="space-y-3">
          <div>
            <label className="text-sm font-medium text-[var(--foreground)]">
              Email
            </label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@university.edu"
              required
              className="mt-1"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-[var(--foreground)]">
              Password
            </label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min 6 characters"
              required
              minLength={6}
              className="mt-1"
            />
          </div>
          {error && (
            <p className="text-sm text-[var(--destructive)]">{error}</p>
          )}
          {message && (
            <p className="text-sm text-[#68b266]">{message}</p>
          )}
          <Button type="submit" className="w-full" disabled={loading}>
            <Mail className="h-4 w-4" />
            {loading
              ? "Please wait..."
              : mode === "login"
              ? "Sign in with Email"
              : "Sign up with Email"}
          </Button>
        </form>

        <p className="mt-4 text-center text-sm text-[var(--muted-foreground)]">
          {mode === "login" ? (
            <>
              Don&apos;t have an account?{" "}
              <button
                onClick={() => setMode("signup")}
                className="font-medium text-[var(--accent)] hover:underline"
              >
                Sign up
              </button>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <button
                onClick={() => setMode("login")}
                className="font-medium text-[var(--accent)] hover:underline"
              >
                Sign in
              </button>
            </>
          )}
        </p>
      </div>
    </div>
  );
}

/* ── Feature Card ──────────────────────────────────────────── */

function FeatureCard({
  icon: Icon,
  title,
  description,
}: {
  icon: React.ElementType;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-2xl bg-[rgba(180,214,211,0.12)] p-6 space-y-4">
      <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-[var(--card)] shadow-sm">
        <Icon className="h-7 w-7 text-[var(--accent)]" />
      </div>
      <h3 className="text-xl font-semibold text-[var(--foreground)]">
        {title}
      </h3>
      <p className="text-sm leading-relaxed text-[var(--muted-foreground)]">
        {description}
      </p>
    </div>
  );
}

/* ── Pricing Card ──────────────────────────────────────────── */

function PricingCard({
  name,
  price,
  description,
  features,
  highlighted,
  onAction,
}: {
  name: string;
  price: string;
  description: string;
  features: string[];
  highlighted?: boolean;
  onAction: () => void;
}) {
  return (
    <Card
      className={`flex flex-col overflow-hidden ${
        highlighted
          ? "bg-[var(--accent)] text-white ring-2 ring-[var(--accent)] scale-[1.02]"
          : ""
      }`}
    >
      <div className="p-6 space-y-3">
        <h3
          className={`text-xl font-semibold ${
            highlighted ? "text-white" : "text-[var(--foreground)]"
          }`}
        >
          {name}
        </h3>
        <p
          className={`text-sm ${
            highlighted ? "text-white/80" : "text-[var(--muted-foreground)]"
          }`}
        >
          {description}
        </p>
        <div className="flex items-baseline gap-1">
          <span
            className={`text-sm ${
              highlighted ? "text-white/70" : "text-[var(--muted-foreground)]"
            }`}
          >
            &euro;
          </span>
          <span
            className={`text-4xl font-bold ${
              highlighted ? "text-white" : "text-[var(--foreground)]"
            }`}
          >
            {price}
          </span>
          <span
            className={`text-sm ${
              highlighted ? "text-white/70" : "text-[var(--muted-foreground)]"
            }`}
          >
            /mo
          </span>
        </div>
      </div>
      <div
        className={`flex-1 space-y-3 rounded-xl p-6 ${
          highlighted ? "bg-white" : "bg-[rgba(180,214,211,0.1)]"
        }`}
      >
        {features.map((f) => (
          <div key={f} className="flex items-start gap-2.5">
            <Check className="h-5 w-5 shrink-0 text-[var(--accent)]" />
            <span className="text-sm text-[var(--foreground)]">{f}</span>
          </div>
        ))}
        <div className="pt-3">
          <Button
            variant={highlighted ? "default" : "outline"}
            className="w-full rounded-xl"
            onClick={onAction}
          >
            {name === "Free" ? "Start for free" : `Go ${name}`}
          </Button>
        </div>
      </div>
    </Card>
  );
}

/* ── Main Landing Page ─────────────────────────────────────── */

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuthStore();
  const [authModal, setAuthModal] = useState<"login" | "signup" | null>(null);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  const features = [
    {
      icon: Brain,
      title: "AI Study Planner",
      description:
        "Intelligent scheduling that adapts to your energy, deadlines, and difficulty. Never miss a study session again.",
    },
    {
      icon: Calendar,
      title: "Calendar Sync",
      description:
        "Two-way Google Calendar integration. Your study blocks appear alongside classes and events automatically.",
    },
    {
      icon: BarChart3,
      title: "Smart Analytics",
      description:
        "Track study hours, completion rates, and productivity trends. Know exactly where your time goes.",
    },
  ];

  const benefits = [
    "AI-powered scheduling that respects your energy levels",
    "Automatic break cadence and burnout prevention",
    "Smart replanning when life gets in the way",
    "Course-aware task prioritization by deadline",
    "Collaborative study group planning",
  ];

  return (
    <div className="min-h-screen bg-[var(--background)]">
      {/* ── Navbar ──────────────────────────────────────── */}
      <header className="sticky top-0 z-40 bg-[var(--background)]/80 backdrop-blur-md border-b border-[var(--border)]">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <Link href="/" className="flex items-center gap-2">
            <Image src="/logo.png" alt="BrainyBuddy" width={32} height={32} />
            <span className="text-xl font-semibold text-[var(--accent)]">
              BrainyBuddy
            </span>
          </Link>
          <nav className="hidden md:flex items-center gap-8 text-sm">
            <a href="#features" className="text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors">
              Features
            </a>
            <a href="#benefits" className="text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors">
              Benefits
            </a>
            <a href="#pricing" className="text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors">
              Pricing
            </a>
          </nav>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setAuthModal("login")}
              className="text-sm font-medium text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
            >
              Login
            </button>
            <Button size="sm" onClick={() => setAuthModal("signup")}>
              Sign Up
            </Button>
          </div>
        </div>
      </header>

      {/* ── Hero ────────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-6 pt-20 pb-16">
        <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
          <div className="space-y-6">
            <h1 className="text-5xl font-bold leading-tight text-[var(--foreground)] lg:text-6xl">
              We&apos;re here to
              <br />
              Boost your{" "}
              <span className="text-[var(--accent)]">Study Game</span>
            </h1>
            <p className="max-w-md text-lg leading-relaxed text-[var(--muted-foreground)]">
              Let&apos;s make your study life more organized using BrainyBuddy&apos;s
              AI-powered planner with smart scheduling, calendar sync, and
              intelligent insights.
            </p>
            <div className="flex items-center gap-4">
              <Button
                size="lg"
                className="rounded-full px-8"
                onClick={() => setAuthModal("signup")}
              >
                Try free trial
              </Button>
              <Link
                href="#features"
                className="flex items-center gap-2 text-sm font-medium text-[var(--foreground)] hover:text-[var(--accent)] transition-colors"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-full border border-[var(--border)]">
                  <ArrowRight className="h-4 w-4" />
                </div>
                Learn more
              </Link>
            </div>
          </div>

          {/* Hero visual */}
          <div className="relative hidden lg:block">
            <div className="relative h-[420px] w-full overflow-hidden rounded-2xl bg-[var(--accent)]">
              {/* Decorative shapes */}
              <div className="absolute -top-20 -right-20 h-60 w-60 rounded-full bg-[rgba(255,255,255,0.1)]" />
              <div className="absolute -bottom-10 -left-10 h-40 w-40 rounded-full bg-[rgba(255,255,255,0.08)]" />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="space-y-4 text-center text-white">
                  <CheckSquare className="mx-auto h-16 w-16 opacity-80" />
                  <p className="text-2xl font-bold">Plan Smarter</p>
                  <p className="text-sm opacity-70">
                    AI schedules your study sessions around your life
                  </p>
                </div>
              </div>
            </div>
            {/* Floating cards */}
            <div className="absolute -left-6 top-8 rounded-xl bg-[var(--card)] p-4 shadow-lg">
              <p className="text-xs text-[var(--muted-foreground)]">
                Active Tasks
              </p>
              <p className="text-2xl font-bold text-[var(--foreground)]">12</p>
            </div>
            <div className="absolute -right-4 bottom-12 rounded-xl bg-[var(--card)] p-4 shadow-lg">
              <p className="text-xs text-[var(--muted-foreground)]">
                Study Hours
              </p>
              <p className="text-2xl font-bold text-[var(--foreground)]">
                4.5h
              </p>
              <div className="mt-1 flex items-center gap-1 text-xs text-[#68b266]">
                <Zap className="h-3 w-3" />
                +12% this week
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ────────────────────────────────────── */}
      <section id="features" className="mx-auto max-w-6xl px-6 py-20">
        <div className="mb-12 max-w-xl">
          <h2 className="text-4xl font-bold text-[var(--foreground)]">
            Features that supercharge your studying
          </h2>
          <p className="mt-4 text-[var(--muted-foreground)]">
            We offer a variety of intelligent features to help you stay on track, manage deadlines, and study more effectively.
          </p>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          {features.map((f) => (
            <FeatureCard key={f.title} {...f} />
          ))}
        </div>
      </section>

      {/* ── Benefits ────────────────────────────────────── */}
      <section id="benefits" className="bg-[rgba(180,214,211,0.1)] py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
            <div className="space-y-6">
              <h2 className="text-4xl font-bold text-[var(--foreground)]">
                What you&apos;ll get with BrainyBuddy
              </h2>
              <div className="space-y-4">
                {benefits.map((b) => (
                  <div key={b} className="flex items-start gap-3">
                    <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--accent)]">
                      <Check className="h-3.5 w-3.5 text-white" />
                    </div>
                    <span className="text-[var(--foreground)]">{b}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex items-center justify-center">
              <div className="grid grid-cols-2 gap-4">
                <Card className="space-y-2 text-center">
                  <Clock className="mx-auto h-8 w-8 text-[var(--accent)]" />
                  <p className="text-2xl font-bold text-[var(--foreground)]">
                    15min
                  </p>
                  <p className="text-xs text-[var(--muted-foreground)]">
                    Smart time slots
                  </p>
                </Card>
                <Card className="space-y-2 text-center">
                  <Shield className="mx-auto h-8 w-8 text-[#5688e0]" />
                  <p className="text-2xl font-bold text-[var(--foreground)]">
                    24/7
                  </p>
                  <p className="text-xs text-[var(--muted-foreground)]">
                    Auto replanning
                  </p>
                </Card>
                <Card className="space-y-2 text-center">
                  <BookOpen className="mx-auto h-8 w-8 text-[#68b266]" />
                  <p className="text-2xl font-bold text-[var(--foreground)]">
                    2-way
                  </p>
                  <p className="text-xs text-[var(--muted-foreground)]">
                    Calendar sync
                  </p>
                </Card>
                <Card className="space-y-2 text-center">
                  <Brain className="mx-auto h-8 w-8 text-[#d58d49]" />
                  <p className="text-2xl font-bold text-[var(--foreground)]">
                    AI
                  </p>
                  <p className="text-xs text-[var(--muted-foreground)]">
                    Study assistant
                  </p>
                </Card>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Pricing ─────────────────────────────────────── */}
      <section id="pricing" className="mx-auto max-w-6xl px-6 py-20">
        <div className="mb-12 text-center">
          <h2 className="text-4xl font-bold text-[var(--foreground)]">
            Choose the plan that fits
          </h2>
          <p className="mt-3 text-[var(--muted-foreground)]">
            Start free and upgrade when you&apos;re ready
          </p>
        </div>
        <div className="grid gap-6 md:grid-cols-3 items-start">
          <PricingCard
            name="Free"
            price="0"
            description="Get started and test your study superpowers"
            features={[
              "15 active tasks",
              "Basic AI scheduling",
              "ICS calendar export",
              "Chat support",
              "Weekly insights",
            ]}
            onAction={() => setAuthModal("signup")}
          />
          <PricingCard
            name="Standard"
            price="8"
            description="Unlock the full power of intelligent planning"
            features={[
              "Unlimited tasks",
              "Full Google Calendar sync",
              "Advanced scheduling engine",
              "Document ingestion",
              "All incoming features",
            ]}
            highlighted
            onAction={() => setAuthModal("signup")}
          />
          <PricingCard
            name="Premium Tutor"
            price="18"
            description="Course-aware AI tutor with advanced features"
            features={[
              "All Standard features",
              "AI tutor (Socratic mode)",
              "Flashcard generation",
              "Practice exams",
              "Collaboration tools",
            ]}
            onAction={() => setAuthModal("signup")}
          />
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────────── */}
      <section className="bg-[#1a1f2e] py-20">
        <div className="mx-auto max-w-6xl px-6 text-center">
          <h2 className="text-4xl font-bold text-white">
            Ready to ace your semester?
          </h2>
          <p className="mx-auto mt-4 max-w-md text-[#8890a4]">
            Join students who plan smarter, study better, and stress less with
            BrainyBuddy.
          </p>
          <div className="mt-8 flex justify-center">
            <Button
              size="lg"
              className="rounded-full px-10"
              onClick={() => setAuthModal("signup")}
            >
              Get Started Free
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────── */}
      <footer className="bg-[#0f1117] py-12">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid gap-8 md:grid-cols-4">
            <div>
              <Link href="/" className="flex items-center gap-2">
                <Image
                  src="/logo.png"
                  alt="BrainyBuddy"
                  width={28}
                  height={28}
                />
                <span className="text-lg font-semibold text-[var(--accent)]">
                  BrainyBuddy
                </span>
              </Link>
              <p className="mt-3 text-sm text-[#8890a4]">
                AI-powered study planner that runs your semester.
              </p>
            </div>
            <div>
              <p className="font-medium text-white text-sm">Product</p>
              <div className="mt-3 space-y-2 text-sm text-[#8890a4]">
                <p>Features</p>
                <p>Pricing</p>
                <p>Changelog</p>
              </div>
            </div>
            <div>
              <p className="font-medium text-white text-sm">Support</p>
              <div className="mt-3 space-y-2 text-sm text-[#8890a4]">
                <p>Help Center</p>
                <p>Contact Us</p>
                <p>Status</p>
              </div>
            </div>
            <div>
              <p className="font-medium text-white text-sm">Legal</p>
              <div className="mt-3 space-y-2 text-sm text-[#8890a4]">
                <p>Privacy Policy</p>
                <p>Terms of Service</p>
              </div>
            </div>
          </div>
          <div className="mt-10 flex items-center justify-between border-t border-[#2d3348] pt-6">
            <p className="text-xs text-[#8890a4]">
              &copy; 2026 BrainyBuddy. All rights reserved.
            </p>
            <div className="flex gap-4 text-xs text-[#8890a4]">
              <span>Terms and Conditions</span>
              <span>Privacy Policy</span>
            </div>
          </div>
        </div>
      </footer>

      {/* ── Auth Modal ──────────────────────────────────── */}
      <AuthModal
        open={authModal !== null}
        onClose={() => setAuthModal(null)}
        mode={authModal ?? "login"}
      />
    </div>
  );
}
