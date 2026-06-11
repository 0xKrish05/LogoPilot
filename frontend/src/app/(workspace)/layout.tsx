"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Sidebar } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";

const TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/automations": "Automations",
  "/queue": "Queue",
  "/accounts": "Instagram Accounts",
  "/billing": "Billing & Plans",
  "/admin": "Admin",
};

export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading, firebaseMissing } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // When Firebase isn't configured yet, allow browsing the workspace UI
    // (read-only preview) instead of locking the user out.
    if (!loading && !user && !firebaseMissing) router.replace("/login");
  }, [user, loading, firebaseMissing, router]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-[3px] border-line border-t-indigo-500" />
      </div>
    );
  }

  const title =
    Object.entries(TITLES).find(([p]) => pathname.startsWith(p))?.[1] ?? "Workspace";

  return (
    <div className="min-h-screen bg-surface-2">
      <Sidebar isAdmin />
      <div className="md:pl-60">
        <Topbar title={title} />
        <main className="mx-auto max-w-6xl animate-fade-up px-6 py-8">
          {firebaseMissing && (
            <div className="mb-6 rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-700 dark:text-amber-400">
              <strong>Preview mode</strong> — Google sign-in isn’t configured
              yet, so live data is unavailable. The UI below shows how your
              workspace will look.
            </div>
          )}
          {children}
        </main>
      </div>
    </div>
  );
}
