"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, apiUpload, authedAssetUrl } from "@/lib/api";
import { useData } from "@/lib/useData";
import { AutomationStatusBadge, QueueStatusBadge } from "@/components/StatusBadge";
import type { Automation, IgAccount, LogoPosition, QueueItem } from "@/lib/types";

const DAY_LABELS = ["Today", "Tomorrow", "Day 3", "Day 4", "Day 5"];

/** Offset (in minutes) of `timeZone` from UTC at the given instant. */
function tzOffsetMinutes(timeZone: string, date: Date): number {
  const dtf = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hour12: false,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  const map: Record<string, string> = {};
  for (const p of dtf.formatToParts(date)) map[p.type] = p.value;
  const hour = map.hour === "24" ? "00" : map.hour;
  const asUTC = Date.UTC(
    Number(map.year),
    Number(map.month) - 1,
    Number(map.day),
    Number(hour),
    Number(map.minute),
    Number(map.second)
  );
  return (asUTC - date.getTime()) / 60000;
}

/** ISO UTC timestamp -> "YYYY-MM-DDTHH:mm:ss" wall-clock string in `timeZone`. */
function toLocalInputValue(iso: string, timeZone: string): string {
  const date = new Date(iso);
  const offset = tzOffsetMinutes(timeZone, date);
  const shifted = new Date(date.getTime() + offset * 60000);
  return shifted.toISOString().slice(0, 19);
}

/** "YYYY-MM-DDTHH:mm[:ss]" wall-clock string in `timeZone` -> ISO UTC timestamp. */
function fromLocalInputValue(value: string, timeZone: string): string {
  const withSeconds = value.length === 16 ? `${value}:00` : value;
  const naiveUtc = new Date(`${withSeconds}Z`);
  const offset = tzOffsetMinutes(timeZone, naiveUtc);
  return new Date(naiveUtc.getTime() - offset * 60000).toISOString();
}

const POSITIONS: { value: LogoPosition; label: string }[] = [
  { value: "top_left", label: "Top left" },
  { value: "top_center", label: "Top center" },
  { value: "top_right", label: "Top right" },
  { value: "center", label: "Center" },
  { value: "bottom_left", label: "Bottom left" },
  { value: "bottom_center", label: "Bottom center" },
  { value: "bottom_right", label: "Bottom right" },
  { value: "full_overlay", label: "Full overlay" },
];

export default function AutomationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const {
    data: automation,
    refresh,
    error,
  } = useData<Automation | null>(`/automations/${id}`, null);
  const { data: queue, refresh: refreshQueue } = useData<QueueItem[]>(
    `/automations/${id}/queue`,
    []
  );
  const [tab, setTab] = useState<"queue" | "settings">("queue");

  if (error) {
    return (
      <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-600 dark:text-rose-400">
        Couldn’t load this automation: {error}
      </div>
    );
  }
  if (!automation) {
    return (
      <div className="flex justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-[3px] border-line border-t-indigo-500" />
      </div>
    );
  }

  const toggleStatus = async () => {
    await api(`/automations/${id}`, {
      method: "PATCH",
      body: JSON.stringify({
        status: automation.status === "active" ? "paused" : "active",
      }),
    });
    refresh();
  };

  const remove = async () => {
    if (!window.confirm(`Delete “${automation.name}” and its queue?`)) return;
    await api(`/automations/${id}`, { method: "DELETE" });
    router.replace("/automations");
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card flex flex-wrap items-center justify-between gap-4 p-5">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-fuchsia-500 text-xl text-white shadow-md">
            ⚡
          </div>
          <div>
            <h2 className="font-display text-lg font-bold">{automation.name}</h2>
            <div className="mt-1 flex items-center gap-2">
              <AutomationStatusBadge status={automation.status} />
              <span className="text-xs text-ink-faint">
                {automation.daily_upload_target} uploads/day · night{" "}
                {automation.night_mode_start}–{automation.night_mode_end}
              </span>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <button onClick={toggleStatus} className="btn-ghost">
            {automation.status === "active" ? "⏸ Pause" : "▶ Activate"}
          </button>
          <button onClick={remove} className="btn-danger">
            Delete
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-xl border border-line bg-surface p-1">
        {(["queue", "settings"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 rounded-lg py-2 text-sm font-semibold capitalize transition ${
              tab === t
                ? "bg-gradient-to-r from-indigo-500 to-violet-500 text-white shadow"
                : "text-ink-soft hover:text-ink"
            }`}
          >
            {t === "queue" ? `🎬 Queue (${queue.length})` : "⚙️ Settings"}
          </button>
        ))}
      </div>

      {tab === "queue" ? (
        <QueueTab automationId={id} automation={automation} queue={queue} refresh={refreshQueue} />
      ) : (
        <SettingsTab automation={automation} refresh={refresh} />
      )}
    </div>
  );
}

function QueueTab({
  automationId,
  automation,
  queue,
  refresh,
}: {
  automationId: string;
  automation: Automation;
  queue: QueueItem[];
  refresh: () => void;
}) {
  const [urls, setUrls] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [editingSchedule, setEditingSchedule] = useState<string | null>(null);
  const [scheduleValue, setScheduleValue] = useState("");
  const [scheduleBusy, setScheduleBusy] = useState<Record<string, boolean>>({});

  // Live status: poll the queue so transitions (queued -> downloading -> ...)
  // appear without a manual page refresh.
  useEffect(() => {
    const id = setInterval(refresh, 10000);
    return () => clearInterval(id);
  }, [refresh]);

  const submit = async () => {
    const list = urls
      .split(/\s+/)
      .map((u) => u.trim())
      .filter(Boolean);
    if (list.length === 0) return;
    setBusy(true);
    setResult(null);
    try {
      const res = await api<{ approved: unknown[]; rejected: unknown[] }>(
        `/automations/${automationId}/queue`,
        { method: "POST", body: JSON.stringify({ urls: list }) }
      );
      setResult(`✅ ${res.approved.length} approved · 🚫 ${res.rejected.length} rejected`);
      setUrls("");
      refresh();
    } catch (e) {
      setResult(`❌ ${e instanceof Error ? e.message : "Failed"}`);
    } finally {
      setBusy(false);
    }
  };

  const retry = async (itemId: string) => {
    await api(`/automations/${automationId}/queue/${itemId}/retry`, { method: "POST" });
    refresh();
  };

  const startEditSchedule = (q: QueueItem) => {
    setEditingSchedule(q.id);
    setScheduleValue(
      q.scheduled_at ? toLocalInputValue(q.scheduled_at, automation.timezone) : ""
    );
  };

  const saveSchedule = async (itemId: string) => {
    if (!scheduleValue) return;
    setScheduleBusy((b) => ({ ...b, [itemId]: true }));
    try {
      await api(`/automations/${automationId}/queue/${itemId}/schedule`, {
        method: "PATCH",
        body: JSON.stringify({
          scheduled_at: fromLocalInputValue(scheduleValue, automation.timezone),
        }),
      });
      setEditingSchedule(null);
      refresh();
    } finally {
      setScheduleBusy((b) => ({ ...b, [itemId]: false }));
    }
  };

  return (
    <div className="space-y-5">
      <div className="card p-5">
        <h3 className="font-display text-sm font-bold">Add reel links</h3>
        <p className="mt-1 text-xs text-ink-soft">
          Paste one or more Instagram reel URLs — one per line. They’ll be
          filtered, scheduled and processed automatically.
        </p>
        <textarea
          className="input mt-3 h-28 resize-y font-mono text-xs"
          placeholder={"https://www.instagram.com/reel/...\nhttps://www.instagram.com/reel/..."}
          value={urls}
          onChange={(e) => setUrls(e.target.value)}
        />
        <div className="mt-3 flex items-center justify-between">
          <span className="text-xs text-ink-faint">{result}</span>
          <button onClick={submit} disabled={busy} className="btn-primary">
            {busy ? "Submitting…" : "Add to queue"}
          </button>
        </div>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line bg-surface-2 text-left text-xs uppercase tracking-wider text-ink-faint">
              <th className="px-5 py-3 font-semibold">Thumbnail</th>
              <th className="px-5 py-3 font-semibold">Source</th>
              <th className="px-5 py-3 font-semibold">Status</th>
              <th className="px-5 py-3 font-semibold">Scheduled</th>
              <th className="px-5 py-3 font-semibold">Result</th>
              <th className="px-5 py-3" />
            </tr>
          </thead>
          <tbody>
            {queue.map((q) => (
              <tr key={q.id} className="border-b border-line/60 transition hover:bg-surface-2/60">
                <td className="px-5 py-3.5">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-lg border border-line bg-surface-2">
                    {q.has_thumbnail ? (
                      <img
                        src={authedAssetUrl(`/automations/${automationId}/queue/${q.id}/thumbnail`)}
                        alt="Reel thumbnail"
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <span className="text-lg">🎞️</span>
                    )}
                  </div>
                </td>
                <td className="max-w-[220px] truncate px-5 py-3.5 text-ink-soft">
                  {q.source_url}
                </td>
                <td className="px-5 py-3.5">
                  <QueueStatusBadge status={q.status} />
                  {q.rejection_reason && (
                    <span className="ml-2 text-xs text-ink-faint">({q.rejection_reason})</span>
                  )}
                </td>
                <td className="px-5 py-3.5 text-xs text-ink-soft">
                  {q.scheduled_at
                    ? new Date(q.scheduled_at).toLocaleString("en-IN", {
                        timeZone: automation.timezone,
                        dateStyle: "medium",
                        timeStyle: "medium",
                      })
                    : "—"}
                </td>
                <td className="max-w-[180px] truncate px-5 py-3.5 text-xs">
                  {q.uploaded_reel_url ? (
                    <a
                      href={q.uploaded_reel_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-brand-500 hover:underline"
                    >
                      View reel ↗
                    </a>
                  ) : q.last_error ? (
                    <span className="text-rose-500">{q.last_error}</span>
                  ) : (
                    "—"
                  )}
                </td>
                <td className="px-5 py-3.5 text-right">
                  <div className="flex items-center justify-end gap-2">
                    {(q.status === "queued" || q.status === "waiting") && (
                      <button
                        onClick={() => startEditSchedule(q)}
                        className="btn-ghost !px-3 !py-1.5 text-xs"
                      >
                        ✏️ Edit
                      </button>
                    )}
                    {(q.status === "failed" ||
                      q.status === "force_stopped" ||
                      q.status === "cookie_expired") && (
                      <button onClick={() => retry(q.id)} className="btn-ghost !px-3 !py-1.5 text-xs">
                        ↻ Retry
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {queue.length === 0 && (
              <tr>
                <td colSpan={6} className="px-5 py-10 text-center text-sm text-ink-faint">
                  Queue is empty — add some reel links above.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {editingSchedule && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          onClick={() => setEditingSchedule(null)}
        >
          <div
            className="card w-full max-w-sm p-5"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="font-display text-sm font-bold">Reschedule reel</h3>
            <p className="mt-1 text-xs text-ink-faint">
              Pick a new date and time ({automation.timezone}) for this reel to be posted.
            </p>
            <input
              type="datetime-local"
              step={1}
              className="input mt-3"
              value={scheduleValue}
              onChange={(e) => setScheduleValue(e.target.value)}
            />
            <div className="mt-4 flex justify-end gap-2">
              <button onClick={() => setEditingSchedule(null)} className="btn-ghost">
                Cancel
              </button>
              <button
                onClick={() => saveSchedule(editingSchedule)}
                disabled={!scheduleValue || scheduleBusy[editingSchedule]}
                className="btn-primary"
              >
                {scheduleBusy[editingSchedule] ? "Saving…" : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SettingsTab({
  automation,
  refresh,
}: {
  automation: Automation;
  refresh: () => void;
}) {
  const { data: igAccounts } = useData<IgAccount[]>("/instagram/accounts", []);
  const [form, setForm] = useState({
    name: automation.name,
    instagram_account_id: automation.instagram_account_id ?? "",
    logo_position: automation.logo_position,
    logo_size_percent: automation.logo_size_percent,
    logo_opacity_percent: automation.logo_opacity_percent,
    chroma_key_color: automation.chroma_key_color ?? "",
    caption_template: automation.caption_template ?? "",
    daily_upload_target: automation.daily_upload_target,
    daily_target_overrides: Array.from(
      { length: 5 },
      (_, i) => automation.daily_target_overrides?.[i] ?? null
    ) as (number | null)[],
    night_mode_start: automation.night_mode_start,
    night_mode_end: automation.night_mode_end,
    min_reel_duration_seconds: automation.min_reel_duration_seconds,
    clipster_submission_url: automation.clipster_submission_url ?? "",
  });
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [logoBusy, setLogoBusy] = useState(false);
  const [logoError, setLogoError] = useState<string | null>(null);
  const [thumbBusy, setThumbBusy] = useState(false);
  const [thumbError, setThumbError] = useState<string | null>(null);
  const [thumbVersion, setThumbVersion] = useState(0);
  const [cookiesBusy, setCookiesBusy] = useState(false);
  const [cookiesError, setCookiesError] = useState<string | null>(null);
  const [igCookiesBusy, setIgCookiesBusy] = useState(false);
  const [igCookiesError, setIgCookiesError] = useState<string | null>(null);

  const set = <K extends keyof typeof form>(k: K, v: (typeof form)[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const save = async () => {
    setBusy(true);
    setSaved(false);
    try {
      await api(`/automations/${automation.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          ...form,
          instagram_account_id: form.instagram_account_id || null,
          chroma_key_color: form.chroma_key_color || null,
          caption_template: form.caption_template || null,
          clipster_submission_url: form.clipster_submission_url || null,
        }),
      });
      setSaved(true);
      refresh();
    } finally {
      setBusy(false);
    }
  };

  const uploadLogo = async (file: File) => {
    setLogoBusy(true);
    setLogoError(null);
    try {
      await apiUpload(`/automations/${automation.id}/logo`, file);
      refresh();
    } catch (e) {
      setLogoError(e instanceof Error ? e.message : "Logo upload failed");
    } finally {
      setLogoBusy(false);
    }
  };

  const uploadThumbnail = async (file: File) => {
    setThumbBusy(true);
    setThumbError(null);
    try {
      await apiUpload(`/automations/${automation.id}/thumbnail`, file);
      setThumbVersion((v) => v + 1);
      refresh();
    } catch (e) {
      setThumbError(e instanceof Error ? e.message : "Thumbnail upload failed");
    } finally {
      setThumbBusy(false);
    }
  };

  const removeThumbnail = async () => {
    setThumbBusy(true);
    try {
      await api(`/automations/${automation.id}/thumbnail`, { method: "DELETE" });
      refresh();
    } finally {
      setThumbBusy(false);
    }
  };

  const uploadClipsterCookies = async (file: File) => {
    setCookiesBusy(true);
    setCookiesError(null);
    try {
      await apiUpload(`/automations/${automation.id}/clipster-cookies`, file);
      refresh();
    } catch (e) {
      setCookiesError(e instanceof Error ? e.message : "Cookie upload failed");
    } finally {
      setCookiesBusy(false);
    }
  };

  const removeClipsterCookies = async () => {
    await api(`/automations/${automation.id}/clipster-cookies`, { method: "DELETE" });
    refresh();
  };

  const uploadInstagramCookies = async (file: File) => {
    setIgCookiesBusy(true);
    setIgCookiesError(null);
    try {
      await apiUpload(`/automations/${automation.id}/instagram-cookies`, file);
      refresh();
    } catch (e) {
      setIgCookiesError(e instanceof Error ? e.message : "Cookie upload failed");
    } finally {
      setIgCookiesBusy(false);
    }
  };

  const removeInstagramCookies = async () => {
    await api(`/automations/${automation.id}/instagram-cookies`, { method: "DELETE" });
    refresh();
  };

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      {/* Logo settings with visual position picker */}
      <div className="card p-5">
        <h3 className="font-display text-sm font-bold">🎨 Logo overlay</h3>

        {/* Logo file upload */}
        <div className="mt-3 flex items-center gap-3 rounded-xl border border-line bg-surface-2 p-3">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-lg border border-line bg-surface">
            {automation.logo_file_path ? (
              automation.logo_type && ["mp4", "webm"].includes(automation.logo_type) ? (
                <video
                  key={automation.logo_file_path}
                  src={authedAssetUrl(`/automations/${automation.id}/logo`)}
                  className="h-full w-full object-contain"
                  muted
                  autoPlay
                  loop
                  playsInline
                />
              ) : (
                <img
                  key={automation.logo_file_path}
                  src={authedAssetUrl(`/automations/${automation.id}/logo`)}
                  alt="Logo thumbnail"
                  className="h-full w-full object-contain"
                />
              )
            ) : (
              <span className="text-2xl">🖼️</span>
            )}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-semibold">
              {automation.logo_file_path ? "Logo uploaded ✓" : "No logo uploaded yet"}
            </p>
            <p className="text-xs text-ink-faint">PNG, JPG, GIF, WEBP, MP4 or WEBM</p>
            {logoError && <p className="mt-1 text-xs text-rose-500">{logoError}</p>}
          </div>
          <label className="btn-ghost shrink-0 cursor-pointer !px-3 !py-1.5 text-xs">
            {logoBusy ? "Uploading…" : automation.logo_file_path ? "Replace" : "Upload"}
            <input
              type="file"
              accept=".png,.jpg,.jpeg,.gif,.webp,.mp4,.webm"
              className="hidden"
              disabled={logoBusy}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) uploadLogo(file);
                e.target.value = "";
              }}
            />
          </label>
        </div>

        {/* Reel thumbnail — one image used as the cover for every uploaded reel */}
        <div className="mt-3 flex items-center gap-3 rounded-xl border border-line bg-surface-2 p-3">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-lg border border-line bg-surface">
            {automation.has_thumbnail ? (
              <img
                key={thumbVersion}
                src={`${authedAssetUrl(`/automations/${automation.id}/thumbnail`)}?v=${thumbVersion}`}
                alt="Reel thumbnail"
                className="h-full w-full object-cover"
              />
            ) : (
              <span className="text-2xl">🖼️</span>
            )}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-semibold">
              {automation.has_thumbnail ? "Reel thumbnail set ✓" : "Reel thumbnail (optional)"}
            </p>
            <p className="text-xs text-ink-faint">
              One image used as the cover for every uploaded reel. PNG, JPG or WEBP.
            </p>
            {thumbError && <p className="mt-1 text-xs text-rose-500">{thumbError}</p>}
          </div>
          <label className="btn-ghost shrink-0 cursor-pointer !px-3 !py-1.5 text-xs">
            {thumbBusy ? "Uploading…" : automation.has_thumbnail ? "Replace" : "Upload"}
            <input
              type="file"
              accept=".png,.jpg,.jpeg,.webp"
              className="hidden"
              disabled={thumbBusy}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) uploadThumbnail(file);
                e.target.value = "";
              }}
            />
          </label>
          {automation.has_thumbnail && (
            <button
              onClick={removeThumbnail}
              disabled={thumbBusy}
              className="btn-ghost shrink-0 !px-3 !py-1.5 text-xs"
            >
              Remove
            </button>
          )}
        </div>

        <div className="mt-4 flex gap-5">
          {/* Phone-shaped preview */}
          <div className="relative h-64 w-36 shrink-0 overflow-hidden rounded-2xl border-2 border-line bg-gradient-to-br from-slate-700 via-slate-800 to-slate-900">
            <div className="absolute inset-0 grid grid-cols-3 grid-rows-3 p-2">
              {POSITIONS.slice(0, 7).map((p) => {
                const cell: Record<string, string> = {
                  top_left: "col-start-1 row-start-1",
                  top_center: "col-start-2 row-start-1",
                  top_right: "col-start-3 row-start-1",
                  center: "col-start-2 row-start-2",
                  bottom_left: "col-start-1 row-start-3",
                  bottom_center: "col-start-2 row-start-3",
                  bottom_right: "col-start-3 row-start-3",
                };
                const active = form.logo_position === p.value;
                return (
                  <button
                    key={p.value}
                    title={p.label}
                    onClick={() => set("logo_position", p.value)}
                    className={`m-0.5 flex items-center justify-center rounded-lg text-[10px] font-bold transition ${cell[p.value]} ${
                      active
                        ? "bg-gradient-to-br from-indigo-500 to-fuchsia-500 text-white shadow-lg"
                        : "bg-white/10 text-white/40 hover:bg-white/20"
                    }`}
                  >
                    LOGO
                  </button>
                );
              })}
            </div>
            {form.logo_position === "full_overlay" && (
              <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-indigo-500/70 to-fuchsia-500/70 text-xs font-bold text-white">
                FULL OVERLAY
              </div>
            )}
          </div>
          <div className="flex-1 space-y-4">
            <button
              onClick={() =>
                set(
                  "logo_position",
                  form.logo_position === "full_overlay" ? "bottom_right" : "full_overlay"
                )
              }
              className={`w-full rounded-xl border py-2 text-xs font-semibold transition ${
                form.logo_position === "full_overlay"
                  ? "border-transparent bg-gradient-to-r from-indigo-500 to-fuchsia-500 text-white"
                  : "border-line text-ink-soft hover:bg-surface-2"
              }`}
            >
              Full-screen overlay mode
            </button>
            <div>
              <label className="label">Size — {form.logo_size_percent}%</label>
              <input
                type="range"
                min={5}
                max={100}
                value={form.logo_size_percent}
                onChange={(e) => set("logo_size_percent", Number(e.target.value))}
                className="w-full accent-indigo-500"
              />
            </div>
            <div>
              <label className="label">Opacity — {form.logo_opacity_percent}%</label>
              <input
                type="range"
                min={10}
                max={100}
                value={form.logo_opacity_percent}
                onChange={(e) => set("logo_opacity_percent", Number(e.target.value))}
                className="w-full accent-fuchsia-500"
              />
            </div>
            <div>
              <label className="label">Chroma key (remove color)</label>
              <input
                className="input"
                placeholder="#00FF00 or empty"
                value={form.chroma_key_color}
                onChange={(e) => set("chroma_key_color", e.target.value)}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Schedule + filters */}
      <div className="card space-y-4 p-5">
        <h3 className="font-display text-sm font-bold">📅 Schedule & filters</h3>
        <div>
          <label className="label">Name</label>
          <input className="input" value={form.name} onChange={(e) => set("name", e.target.value)} />
        </div>
        <div>
          <label className="label">Instagram account</label>
          <select
            className="input"
            value={form.instagram_account_id}
            onChange={(e) => set("instagram_account_id", e.target.value)}
          >
            <option value="">— Not connected —</option>
            {igAccounts.map((a) => (
              <option key={a.id} value={a.id}>
                @{a.username}
              </option>
            ))}
          </select>
          {igAccounts.length === 0 && (
            <p className="mt-1 text-xs text-ink-faint">
              No Instagram accounts connected yet — go to Accounts to connect one.
            </p>
          )}
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Uploads / day</label>
            <input
              type="number"
              min={1}
              className="input"
              value={form.daily_upload_target}
              onChange={(e) => set("daily_upload_target", Number(e.target.value))}
            />
          </div>
          <div>
            <label className="label">Min duration (sec)</label>
            <input
              type="number"
              min={0}
              className="input"
              value={form.min_reel_duration_seconds}
              onChange={(e) => set("min_reel_duration_seconds", Number(e.target.value))}
            />
          </div>
          <div className="col-span-2">
            <label className="label">Next 5 days — upload targets</label>
            <p className="-mt-1 mb-2 text-xs text-ink-faint">
              Override how many reels go out on each of the next 5 days — handy when bulk-adding
              hundreds of links. Leave blank to use the default ({form.daily_upload_target}/day).
            </p>
            <div className="grid grid-cols-5 gap-2">
              {DAY_LABELS.map((label, i) => (
                <div key={label}>
                  <label className="label !text-[10px]">{label}</label>
                  <input
                    type="number"
                    min={0}
                    placeholder={String(form.daily_upload_target)}
                    className="input !px-2 text-center"
                    value={form.daily_target_overrides[i] ?? ""}
                    onChange={(e) => {
                      const raw = e.target.value;
                      const next = [...form.daily_target_overrides];
                      next[i] = raw === "" ? null : Number(raw);
                      set("daily_target_overrides", next);
                    }}
                  />
                </div>
              ))}
            </div>
          </div>
          <div>
            <label className="label">Night mode start</label>
            <input
              type="time"
              className="input"
              value={form.night_mode_start}
              onChange={(e) => set("night_mode_start", e.target.value)}
            />
          </div>
          <div>
            <label className="label">Night mode end</label>
            <input
              type="time"
              className="input"
              value={form.night_mode_end}
              onChange={(e) => set("night_mode_end", e.target.value)}
            />
          </div>
        </div>
        <div>
          <label className="label">Caption template</label>
          <textarea
            className="input h-20 resize-y"
            placeholder="Your caption… {original_caption} is replaced automatically"
            value={form.caption_template}
            onChange={(e) => set("caption_template", e.target.value)}
          />
        </div>
        <div>
          <label className="label">Clipster submission URL</label>
          <input
            className="input"
            placeholder="https://clipster…"
            value={form.clipster_submission_url}
            onChange={(e) => set("clipster_submission_url", e.target.value)}
          />
        </div>
        <div>
          <label className="label">
            Clipster cookies{" "}
            {automation.has_clipster_cookies && (
              <span className="ml-1 text-emerald-500">✓ saved</span>
            )}
          </label>
          <div className="flex items-center gap-3 rounded-xl border border-line bg-surface-2 p-3">
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold">
                {automation.has_clipster_cookies
                  ? "cookies.txt uploaded ✓"
                  : "No Clipster cookies uploaded yet"}
              </p>
              <p className="text-xs text-ink-faint">
                Export with the &quot;Get cookies.txt LOCALLY&quot; browser extension while
                logged into Clipster, then upload the file here.
              </p>
              {cookiesError && <p className="mt-1 text-xs text-rose-500">{cookiesError}</p>}
            </div>
            {automation.has_clipster_cookies && (
              <button onClick={removeClipsterCookies} className="btn-ghost shrink-0 !px-3 !py-1.5 text-xs">
                Remove
              </button>
            )}
            <label className="btn-ghost shrink-0 cursor-pointer !px-3 !py-1.5 text-xs">
              {cookiesBusy ? "Uploading…" : automation.has_clipster_cookies ? "Replace" : "Upload"}
              <input
                type="file"
                accept=".txt"
                className="hidden"
                disabled={cookiesBusy}
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) uploadClipsterCookies(file);
                  e.target.value = "";
                }}
              />
            </label>
          </div>
          <p className="mt-1 text-xs text-ink-faint">
            Stored encrypted and used by the worker to submit your edited reels to Clipster.
          </p>
        </div>
        <div>
          <label className="label">
            Instagram session cookies{" "}
            {automation.has_instagram_cookies && (
              <span className="ml-1 text-emerald-500">✓ saved</span>
            )}
          </label>
          <div className="flex items-center gap-3 rounded-xl border border-line bg-surface-2 p-3">
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold">
                {automation.has_instagram_cookies
                  ? "cookies.txt uploaded ✓"
                  : "No Instagram cookies uploaded (optional)"}
              </p>
              <p className="text-xs text-ink-faint">
                Some reels require a logged-in session to download. Export with the &quot;Get
                cookies.txt LOCALLY&quot; browser extension while logged into Instagram, then
                upload the file here.
              </p>
              {igCookiesError && <p className="mt-1 text-xs text-rose-500">{igCookiesError}</p>}
            </div>
            {automation.has_instagram_cookies && (
              <button onClick={removeInstagramCookies} className="btn-ghost shrink-0 !px-3 !py-1.5 text-xs">
                Remove
              </button>
            )}
            <label className="btn-ghost shrink-0 cursor-pointer !px-3 !py-1.5 text-xs">
              {igCookiesBusy ? "Uploading…" : automation.has_instagram_cookies ? "Replace" : "Upload"}
              <input
                type="file"
                accept=".txt"
                className="hidden"
                disabled={igCookiesBusy}
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) uploadInstagramCookies(file);
                  e.target.value = "";
                }}
              />
            </label>
          </div>
          <p className="mt-1 text-xs text-ink-faint">
            Stored encrypted and used by the worker to download restricted/private reels via yt-dlp.
          </p>
        </div>
      </div>

      <div className="flex items-center justify-end gap-3 lg:col-span-2">
        {saved && <span className="text-sm font-semibold text-emerald-500">✓ Saved</span>}
        <button onClick={save} disabled={busy} className="btn-primary !px-8">
          {busy ? "Saving…" : "Save settings"}
        </button>
      </div>
    </div>
  );
}
