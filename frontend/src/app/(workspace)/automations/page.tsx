"use client";

import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useData } from "@/lib/useData";
import { AutomationStatusBadge } from "@/components/StatusBadge";
import { EmptyState } from "@/components/EmptyState";
import type { Automation, IgAccount } from "@/lib/types";

export default function AutomationsPage() {
  const { data: automations, refresh, error } = useData<Automation[]>("/automations", []);
  const [showCreate, setShowCreate] = useState(false);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-ink-soft">
          Each automation pairs a logo + schedule with one Instagram account.
        </p>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          + New automation
        </button>
      </div>

      {error && (
        <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-600 dark:text-rose-400">
          Couldn’t load automations: {error}
        </div>
      )}

      {automations.length === 0 ? (
        <EmptyState
          icon="⚡"
          title="No automations yet"
          body="Create one to start collecting reels, branding them with your logo and posting on schedule."
          action={
            <button onClick={() => setShowCreate(true)} className="btn-primary">
              Create automation
            </button>
          }
        />
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {automations.map((a) => (
            <Link
              key={a.id}
              href={`/automations/${a.id}`}
              className="card group p-5 transition-all duration-200 hover:-translate-y-1 hover:shadow-glow"
            >
              <div className="flex items-start justify-between">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-fuchsia-500 text-lg text-white shadow-md">
                  ⚡
                </div>
                <AutomationStatusBadge status={a.status} />
              </div>
              <h3 className="mt-4 font-display text-base font-bold group-hover:text-brand-500">
                {a.name}
              </h3>
              <div className="mt-3 flex flex-wrap gap-2 text-xs text-ink-soft">
                <span className="rounded-lg bg-surface-2 px-2 py-1">
                  🎯 {a.daily_upload_target}/day
                </span>
                <span className="rounded-lg bg-surface-2 px-2 py-1">
                  🌙 {a.night_mode_start}–{a.night_mode_end}
                </span>
                <span className="rounded-lg bg-surface-2 px-2 py-1">
                  📦 cap {a.queue_capacity}
                </span>
              </div>
              {a.clipster_error && (
                <p className="mt-3 truncate rounded-lg bg-rose-500/10 px-2 py-1 text-xs text-rose-500">
                  ⚠ {a.clipster_error}
                </p>
              )}
            </Link>
          ))}
        </div>
      )}

      {showCreate && (
        <CreateAutomationModal
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            refresh();
          }}
        />
      )}
    </div>
  );
}

function CreateAutomationModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const { data: igAccounts } = useData<IgAccount[]>("/instagram/accounts", []);
  const [name, setName] = useState("");
  const [instagramAccountId, setInstagramAccountId] = useState("");
  const [dailyTarget, setDailyTarget] = useState(5);
  const [minDuration, setMinDuration] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    if (!name.trim()) {
      setError("Give your automation a name.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api("/automations", {
        method: "POST",
        body: JSON.stringify({
          name: name.trim(),
          instagram_account_id: instagramAccountId || null,
          daily_upload_target: dailyTarget,
          min_reel_duration_seconds: minDuration,
        }),
      });
      onCreated();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create");
      setBusy(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="card w-full max-w-md animate-fade-up p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="font-display text-lg font-bold">New automation</h2>
        <p className="mt-1 text-sm text-ink-soft">
          You can fine-tune logo placement and schedule after creating it.
        </p>

        <div className="mt-6 space-y-4">
          <div>
            <label className="label">Name</label>
            <input
              className="input"
              placeholder="e.g. Fitness reels — main account"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
            />
          </div>
          <div>
            <label className="label">Instagram account</label>
            <select
              className="input"
              value={instagramAccountId}
              onChange={(e) => setInstagramAccountId(e.target.value)}
            >
              <option value="">— Choose later —</option>
              {igAccounts.map((a) => (
                <option key={a.id} value={a.id}>
                  @{a.username}
                </option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Uploads / day</label>
              <input
                type="number"
                min={1}
                className="input"
                value={dailyTarget}
                onChange={(e) => setDailyTarget(Number(e.target.value))}
              />
            </div>
            <div>
              <label className="label">Min duration (sec)</label>
              <input
                type="number"
                min={0}
                className="input"
                value={minDuration}
                onChange={(e) => setMinDuration(Number(e.target.value))}
              />
            </div>
          </div>
        </div>

        {error && (
          <p className="mt-4 rounded-xl bg-rose-500/10 p-3 text-xs text-rose-500">{error}</p>
        )}

        <div className="mt-6 flex justify-end gap-3">
          <button onClick={onClose} className="btn-ghost">
            Cancel
          </button>
          <button onClick={submit} disabled={busy} className="btn-primary">
            {busy ? "Creating…" : "Create automation"}
          </button>
        </div>
      </div>
    </div>
  );
}
