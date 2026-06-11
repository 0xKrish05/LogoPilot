"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { StatCard } from "@/components/StatCard";
import { QueueStatusBadge } from "@/components/StatusBadge";
import { FadeUp, StaggerGrid, StaggerItem } from "@/components/Motion";
import { useData } from "@/lib/useData";
import type { Automation, QueueItem, QueueStatus } from "@/lib/types";

const PIPELINE: { status: QueueStatus; label: string; color: string }[] = [
  { status: "queued", label: "Queued", color: "from-sky-400 to-sky-600" },
  { status: "downloading", label: "Downloading", color: "from-cyan-400 to-cyan-600" },
  { status: "editing", label: "Editing", color: "from-violet-400 to-violet-600" },
  { status: "uploading", label: "Uploading", color: "from-indigo-400 to-indigo-600" },
  { status: "submitting", label: "Submitting", color: "from-fuchsia-400 to-fuchsia-600" },
  { status: "completed", label: "Completed", color: "from-emerald-400 to-emerald-600" },
];

export default function DashboardPage() {
  const { data: automations } = useData<Automation[]>("/automations", []);

  const active = automations.filter((a) => a.status === "active").length;
  const errored = automations.filter((a) => a.status === "error").length;
  const dailyTarget = automations.reduce((s, a) => s + (a.daily_upload_target ?? 0), 0);

  return (
    <div className="space-y-8">
      {/* Hero strip */}
      <FadeUp className="card relative overflow-hidden bg-gradient-to-r from-indigo-600 via-violet-600 to-fuchsia-600 p-7 text-white">
        <motion.div
          className="absolute -right-10 -top-16 h-48 w-48 rounded-full bg-white/10 blur-2xl"
          animate={{ x: [0, 20, 0], y: [0, 15, 0] }}
          transition={{ duration: 14, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute -bottom-20 right-32 h-40 w-40 rounded-full bg-fuchsia-300/20 blur-2xl"
          animate={{ x: [0, -15, 0], y: [0, -20, 0] }}
          transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
        />
        <h2 className="font-display text-2xl font-bold">
          Your pipeline at a glance ✨
        </h2>
        <p className="mt-1 max-w-lg text-sm text-white/80">
          {active > 0
            ? `${active} automation${active === 1 ? "" : "s"} working for you right now.`
            : "No active automations yet — create one and drop in your first reel links."}
        </p>
        <Link
          href="/automations"
          className="mt-5 inline-flex items-center gap-2 rounded-xl bg-white px-5 py-2.5 text-sm font-bold text-indigo-600 shadow-lg transition hover:bg-indigo-50"
        >
          ⚡ {automations.length > 0 ? "Manage automations" : "Create your first automation"}
        </Link>
      </FadeUp>

      {/* Stats */}
      <StaggerGrid className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StaggerItem><StatCard label="Automations" value={automations.length} hint={`${active} active`} icon="⚡" accent="indigo" /></StaggerItem>
        <StaggerItem><StatCard label="Daily target" value={dailyTarget} hint="uploads / day across all" icon="🎯" accent="sky" /></StaggerItem>
        <StaggerItem><StatCard label="Needs attention" value={errored} hint={errored ? "automation errors" : "all clear"} icon={errored ? "🚨" : "✅"} accent={errored ? "rose" : "emerald"} /></StaggerItem>
        <StaggerItem><StatCard label="Platform" value="Instagram" hint="YouTube & TikTok soon" icon="📸" accent="fuchsia" /></StaggerItem>
      </StaggerGrid>

      {/* Pipeline stages */}
      <FadeUp delay={0.1} className="card p-6">
        <h3 className="font-display text-base font-bold">Pipeline stages</h3>
        <p className="mt-1 text-sm text-ink-soft">
          Every reel travels through these stages automatically.
        </p>
        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {PIPELINE.map((p, i) => (
            <motion.div
              key={p.status}
              whileHover={{ y: -3, scale: 1.03 }}
              className="group relative rounded-xl border border-line bg-surface-2 p-4 text-center transition-colors hover:border-transparent hover:shadow-glow"
            >
              <div
                className={`mx-auto flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br text-xs font-bold text-white ${p.color}`}
              >
                {i + 1}
              </div>
              <p className="mt-2.5 text-xs font-semibold">{p.label}</p>
            </motion.div>
          ))}
        </div>
      </FadeUp>

      {/* Per-automation queues */}
      <StaggerGrid className="grid gap-5 lg:grid-cols-2">
        {automations.slice(0, 4).map((a) => (
          <StaggerItem key={a.id}><AutomationQueuePreview automation={a} /></StaggerItem>
        ))}
        {automations.length === 0 && (
          <div className="card p-6 lg:col-span-2">
            <p className="text-center text-sm text-ink-soft">
              Recent activity will appear here once your first automation is running.
            </p>
          </div>
        )}
      </StaggerGrid>
    </div>
  );
}

function AutomationQueuePreview({ automation }: { automation: Automation }) {
  const { data: items } = useData<QueueItem[]>(
    `/automations/${automation.id}/queue`,
    []
  );

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between">
        <Link
          href={`/automations/${automation.id}`}
          className="font-display text-sm font-bold hover:text-brand-500"
        >
          {automation.name}
        </Link>
        <span className="text-xs text-ink-faint">{items.length} items</span>
      </div>
      <ul className="mt-4 space-y-2.5">
        {items.slice(0, 4).map((q) => (
          <li key={q.id} className="flex items-center justify-between gap-3 text-sm">
            <span className="truncate text-ink-soft">{q.source_url}</span>
            <QueueStatusBadge status={q.status} />
          </li>
        ))}
        {items.length === 0 && (
          <li className="text-sm text-ink-faint">Queue is empty.</li>
        )}
      </ul>
    </div>
  );
}
