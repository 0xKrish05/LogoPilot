"use client";

import { EmptyState } from "@/components/EmptyState";

export default function AccountsPage() {
  return (
    <div className="space-y-6">
      <div className="card relative overflow-hidden bg-gradient-to-r from-fuchsia-600 via-pink-600 to-rose-500 p-7 text-white">
        <div className="absolute -right-8 -top-12 h-40 w-40 rounded-full bg-white/10 blur-2xl" />
        <h2 className="font-display text-xl font-bold">📸 Instagram accounts</h2>
        <p className="mt-1 max-w-lg text-sm text-white/85">
          Connect your Instagram Business accounts so LogoPilot can publish
          branded reels on your behalf via the official Instagram API.
        </p>
      </div>

      <EmptyState
        icon="🔗"
        title="Instagram connection coming online soon"
        body="The platform owner is finishing the Meta App setup. Once live, you'll connect accounts here with one click — no passwords, just the official Instagram login."
      />
    </div>
  );
}
