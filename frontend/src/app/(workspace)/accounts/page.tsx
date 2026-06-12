"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { EmptyState } from "@/components/EmptyState";
import { FadeUp, StaggerGrid, StaggerItem } from "@/components/Motion";
import { api, ApiError } from "@/lib/api";
import { useData } from "@/lib/useData";
import type { IgAccount } from "@/lib/types";

const ERROR_MESSAGES: Record<string, string> = {
  access_denied: "Instagram authorization was cancelled or denied.",
  invalid_state: "Something went wrong with the connection request. Please try again.",
  token_exchange_failed: "Could not verify Instagram authorization. Please try again.",
  no_instagram_account: "Could not read your Instagram profile. Make sure your Instagram account is set to Business/Professional.",
  user_not_found: "Account lookup failed. Please sign in again and retry.",
  account_limit_reached: "You've reached the Instagram account limit for your plan. Upgrade or disconnect an account to add another.",
};

export default function AccountsPage() {
  const { data: accounts, refresh } = useData<IgAccount[]>("/instagram/accounts", []);
  const params = useSearchParams();
  const router = useRouter();
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    const errCode = params.get("error");
    if (errCode) {
      setError(ERROR_MESSAGES[errCode] ?? "Something went wrong connecting Instagram.");
      router.replace("/accounts");
    } else if (params.get("connected")) {
      setNotice("Instagram account connected successfully! 🎉");
      refresh();
      router.replace("/accounts");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  const handleConnect = async () => {
    setConnecting(true);
    setError(null);
    try {
      const { url } = await api<{ url: string }>("/instagram/connect");
      window.location.href = url;
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not start the Instagram connection.");
      setConnecting(false);
    }
  };

  const handleDisconnect = async (id: string) => {
    if (!confirm("Disconnect this Instagram account? Automations using it will stop posting.")) return;
    await api(`/instagram/accounts/${id}`, { method: "DELETE" });
    refresh();
  };

  return (
    <div className="space-y-6">
      <FadeUp className="card relative overflow-hidden bg-gradient-to-r from-fuchsia-600 via-pink-600 to-rose-500 p-7 text-white">
        <motion.div
          className="absolute -right-8 -top-12 h-40 w-40 rounded-full bg-white/10 blur-2xl"
          animate={{ x: [0, 15, 0], y: [0, 10, 0] }}
          transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
        />
        <h2 className="font-display text-xl font-bold">📸 Instagram accounts</h2>
        <p className="mt-1 max-w-lg text-sm text-white/85">
          Connect your Instagram Business accounts so LogoPilot can publish
          branded reels on your behalf via the official Instagram API.
        </p>
        <motion.button
          whileHover={{ scale: 1.03, y: -1 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleConnect}
          disabled={connecting}
          className="mt-5 inline-flex items-center gap-2 rounded-xl bg-white px-5 py-2.5 text-sm font-bold text-rose-600 shadow-lg transition hover:bg-rose-50 disabled:opacity-60"
        >
          {connecting ? "Redirecting…" : "🔗 Connect Instagram account"}
        </motion.button>
      </FadeUp>

      {notice && (
        <FadeUp className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-300">
          {notice}
        </FadeUp>
      )}
      {error && (
        <FadeUp className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-300">
          {error}
        </FadeUp>
      )}

      {accounts.length === 0 ? (
        <EmptyState
          icon="🔗"
          title="No Instagram accounts connected yet"
          body="Click “Connect Instagram account” above and sign in with Facebook to link the Instagram Business account you want LogoPilot to post to."
        />
      ) : (
        <StaggerGrid className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {accounts.map((a) => (
            <StaggerItem key={a.id}>
              <motion.div whileHover={{ y: -3 }} className="card flex items-center gap-4 p-5">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-fuchsia-500 to-rose-500 text-xl text-white">
                  📸
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-display text-sm font-bold">@{a.username}</p>
                  <p className="text-xs text-ink-faint">
                    {a.is_active ? "Active" : "Inactive"} · ID {a.ig_user_id}
                  </p>
                </div>
                <button
                  onClick={() => handleDisconnect(a.id)}
                  className="shrink-0 rounded-lg border border-line px-2.5 py-1.5 text-xs font-semibold text-ink-soft transition hover:border-rose-300 hover:text-rose-500"
                >
                  Disconnect
                </button>
              </motion.div>
            </StaggerItem>
          ))}
        </StaggerGrid>
      )}
    </div>
  );
}
