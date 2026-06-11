"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { LogoWordmark } from "@/components/Logo";

export default function LoginPage() {
  const { user, loading, firebaseMissing, signInWithGoogle } = useAuth();
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && user) router.replace("/dashboard");
  }, [user, loading, router]);

  const handleSignIn = async () => {
    setBusy(true);
    setError(null);
    try {
      await signInWithGoogle();
      router.replace("/dashboard");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign-in failed. Try again.");
      setBusy(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-white px-6 text-slate-900">
      <div className="w-full max-w-sm animate-fade-up">
        <div className="flex justify-center">
          <Link href="/">
            <LogoWordmark size={36} />
          </Link>
        </div>

        <div className="mt-10 rounded-3xl border border-slate-200 bg-white p-8 shadow-[0_8px_40px_rgb(0_0_0/0.06)]">
          <h1 className="text-center font-display text-2xl font-bold tracking-tight">
            Welcome back
          </h1>
          <p className="mt-2 text-center text-sm text-slate-500">
            Sign in to your workspace. New here? Your free trial starts the
            moment you sign in.
          </p>

          {firebaseMissing ? (
            <div className="mt-8 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700">
              <strong>Setup pending:</strong> Google sign-in isn’t configured on
              this server yet (Firebase keys missing). The admin needs to set{" "}
              <code className="rounded bg-amber-100 px-1">NEXT_PUBLIC_FIREBASE_CONFIG</code>.
            </div>
          ) : (
            <button
              onClick={handleSignIn}
              disabled={busy}
              className="mt-8 flex w-full items-center justify-center gap-3 rounded-xl border border-slate-200 bg-white py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 hover:shadow disabled:opacity-50"
            >
              <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden>
                <path fill="#FFC107" d="M43.6 20.1H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.2 8 3l5.7-5.7C34.3 6.1 29.4 4 24 4 13 4 4 13 4 24s9 20 20 20 20-9 20-20c0-1.3-.1-2.6-.4-3.9z"/>
                <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.2 8 3l5.7-5.7C34.3 6.1 29.4 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/>
                <path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z"/>
                <path fill="#1976D2" d="M43.6 20.1H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C36.9 39.2 44 34 44 24c0-1.3-.1-2.6-.4-3.9z"/>
              </svg>
              {busy ? "Signing in…" : "Continue with Google"}
            </button>
          )}

          {error && (
            <p className="mt-4 rounded-xl bg-rose-50 p-3 text-center text-xs text-rose-600">
              {error}
            </p>
          )}
        </div>

        <p className="mt-6 text-center text-xs text-slate-400">
          By continuing you agree to fair use of connected Instagram accounts.
        </p>
      </div>
    </main>
  );
}
