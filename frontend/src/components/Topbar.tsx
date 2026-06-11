"use client";

import { useAuth } from "@/lib/auth";
import { ThemeToggle } from "./ThemeToggle";

export function Topbar({ title }: { title: string }) {
  const { user, firebaseMissing, signOut } = useAuth();

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-line bg-surface/80 px-6 backdrop-blur-md">
      <h1 className="font-display text-xl font-bold tracking-tight">{title}</h1>
      <div className="flex items-center gap-3">
        <ThemeToggle />
        {firebaseMissing ? (
          <span className="hidden rounded-full bg-amber-500/10 px-3 py-1.5 text-xs font-semibold text-amber-600 dark:text-amber-400 sm:inline">
            ⚠ Auth not configured
          </span>
        ) : user ? (
          <div className="flex items-center gap-2.5">
            {user.photoURL ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={user.photoURL}
                alt=""
                className="h-9 w-9 rounded-full ring-2 ring-indigo-500/40"
              />
            ) : (
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-fuchsia-500 text-sm font-bold text-white">
                {(user.displayName ?? user.email ?? "?").charAt(0).toUpperCase()}
              </div>
            )}
            <button onClick={() => signOut()} className="btn-ghost !px-3 !py-1.5 text-xs">
              Sign out
            </button>
          </div>
        ) : null}
      </div>
    </header>
  );
}
