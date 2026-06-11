import type { AutomationStatus, QueueStatus } from "@/lib/types";

const QUEUE_STYLES: Record<QueueStatus, { bg: string; dot: string; label: string; live?: boolean }> = {
  draft: { bg: "bg-slate-500/10 text-slate-500 dark:text-slate-400", dot: "bg-slate-400", label: "Draft" },
  queued: { bg: "bg-sky-500/10 text-sky-600 dark:text-sky-400", dot: "bg-sky-500", label: "Queued" },
  waiting: { bg: "bg-amber-500/10 text-amber-600 dark:text-amber-400", dot: "bg-amber-500", label: "Waiting" },
  downloading: { bg: "bg-cyan-500/10 text-cyan-600 dark:text-cyan-400", dot: "bg-cyan-500", label: "Downloading", live: true },
  editing: { bg: "bg-violet-500/10 text-violet-600 dark:text-violet-400", dot: "bg-violet-500", label: "Editing", live: true },
  uploading: { bg: "bg-indigo-500/10 text-indigo-600 dark:text-indigo-400", dot: "bg-indigo-500", label: "Uploading", live: true },
  submitting: { bg: "bg-fuchsia-500/10 text-fuchsia-600 dark:text-fuchsia-400", dot: "bg-fuchsia-500", label: "Submitting", live: true },
  completed: { bg: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400", dot: "bg-emerald-500", label: "Completed" },
  retrying: { bg: "bg-orange-500/10 text-orange-600 dark:text-orange-400", dot: "bg-orange-500", label: "Retrying", live: true },
  failed: { bg: "bg-rose-500/10 text-rose-600 dark:text-rose-400", dot: "bg-rose-500", label: "Failed" },
  force_stopped: { bg: "bg-red-500/10 text-red-600 dark:text-red-400", dot: "bg-red-600", label: "Force stopped" },
  rejected: { bg: "bg-pink-500/10 text-pink-600 dark:text-pink-400", dot: "bg-pink-500", label: "Rejected" },
};

export function QueueStatusBadge({ status }: { status: QueueStatus }) {
  const s = QUEUE_STYLES[status] ?? QUEUE_STYLES.draft;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${s.bg}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${s.dot} ${s.live ? "animate-pulse-dot" : ""}`} />
      {s.label}
    </span>
  );
}

const AUTOMATION_STYLES: Record<AutomationStatus, { bg: string; dot: string; label: string }> = {
  active: { bg: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400", dot: "bg-emerald-500", label: "Active" },
  paused: { bg: "bg-amber-500/10 text-amber-600 dark:text-amber-400", dot: "bg-amber-500", label: "Paused" },
  error: { bg: "bg-rose-500/10 text-rose-600 dark:text-rose-400", dot: "bg-rose-500", label: "Error" },
};

export function AutomationStatusBadge({ status }: { status: AutomationStatus }) {
  const s = AUTOMATION_STYLES[status] ?? AUTOMATION_STYLES.paused;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${s.bg}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${s.dot}`} />
      {s.label}
    </span>
  );
}
