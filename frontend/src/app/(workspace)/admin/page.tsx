"use client";

import { StatCard } from "@/components/StatCard";
import { useData } from "@/lib/useData";

interface Overview {
  total_users: number;
  trial_users: number;
  active_subscriptions: number;
  total_automations: number;
  queue_size: number;
  failed_jobs: number;
}

const EMPTY: Overview = {
  total_users: 0,
  trial_users: 0,
  active_subscriptions: 0,
  total_automations: 0,
  queue_size: 0,
  failed_jobs: 0,
};

export default function AdminPage() {
  const { data, error } = useData<Overview>("/admin/overview", EMPTY);

  return (
    <div className="space-y-8">
      <div className="card relative overflow-hidden bg-gradient-to-r from-slate-800 via-slate-900 to-black p-7 text-white">
        <div className="absolute -right-10 -top-12 h-44 w-44 rounded-full bg-indigo-500/20 blur-3xl" />
        <h2 className="font-display text-xl font-bold">🛡️ Platform overview</h2>
        <p className="mt-1 text-sm text-white/70">
          Live metrics across all tenants. Visible to admins only.
        </p>
      </div>

      {error && (
        <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-700 dark:text-amber-400">
          {error.includes("403") || error.toLowerCase().includes("admin")
            ? "Your account doesn't have admin access."
            : `Couldn't load metrics: ${error}`}
        </div>
      )}

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard label="Total users" value={data.total_users} icon="👥" accent="indigo" />
        <StatCard label="On trial" value={data.trial_users} icon="⏳" accent="amber" />
        <StatCard label="Paid subscriptions" value={data.active_subscriptions} icon="💎" accent="emerald" />
        <StatCard label="Automations" value={data.total_automations} icon="⚡" accent="fuchsia" />
        <StatCard label="Items in pipeline" value={data.queue_size} icon="🎬" accent="sky" />
        <StatCard label="Force-stopped jobs" value={data.failed_jobs} icon="🚨" accent="rose" />
      </div>
    </div>
  );
}
