"use client";

import Link from "next/link";
import { useData } from "@/lib/useData";
import { QueueStatusBadge } from "@/components/StatusBadge";
import { EmptyState } from "@/components/EmptyState";
import type { Automation, QueueItem } from "@/lib/types";

export default function GlobalQueuePage() {
  const { data: automations } = useData<Automation[]>("/automations", []);

  if (automations.length === 0) {
    return (
      <EmptyState
        icon="🎬"
        title="Nothing in the pipeline"
        body="Create an automation and add reel links — every item across all your automations will show up here."
        action={
          <Link href="/automations" className="btn-primary">
            Go to automations
          </Link>
        }
      />
    );
  }

  return (
    <div className="space-y-6">
      {automations.map((a) => (
        <AutomationQueueSection key={a.id} automation={a} />
      ))}
    </div>
  );
}

function AutomationQueueSection({ automation }: { automation: Automation }) {
  const { data: queue } = useData<QueueItem[]>(
    `/automations/${automation.id}/queue`,
    []
  );

  const counts = queue.reduce<Record<string, number>>((acc, q) => {
    acc[q.status] = (acc[q.status] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="card overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line bg-surface-2/60 px-5 py-4">
        <Link
          href={`/automations/${automation.id}`}
          className="font-display text-sm font-bold hover:text-brand-500"
        >
          ⚡ {automation.name}
        </Link>
        <div className="flex flex-wrap gap-1.5 text-xs">
          {Object.entries(counts).map(([status, n]) => (
            <span key={status} className="rounded-lg bg-surface px-2 py-1 font-semibold text-ink-soft">
              {n} {status.replace("_", " ")}
            </span>
          ))}
          {queue.length === 0 && <span className="text-ink-faint">empty</span>}
        </div>
      </div>
      {queue.length > 0 && (
        <ul className="divide-y divide-line/60">
          {queue.slice(0, 8).map((q) => (
            <li key={q.id} className="flex items-center justify-between gap-4 px-5 py-3 text-sm">
              <span className="truncate text-ink-soft">{q.source_url}</span>
              <span className="flex shrink-0 items-center gap-3">
                {q.scheduled_at && (
                  <span className="hidden text-xs text-ink-faint sm:inline">
                    {new Date(q.scheduled_at).toLocaleString()}
                  </span>
                )}
                <QueueStatusBadge status={q.status} />
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
