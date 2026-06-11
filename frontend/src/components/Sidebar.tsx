"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogoWordmark } from "./Logo";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/automations", label: "Automations", icon: "⚡" },
  { href: "/queue", label: "Queue", icon: "🎬" },
  { href: "/accounts", label: "IG Accounts", icon: "📸" },
  { href: "/billing", label: "Billing", icon: "💳" },
];

const ADMIN_NAV = [{ href: "/admin", label: "Admin", icon: "🛡️" }];

export function Sidebar({ isAdmin }: { isAdmin?: boolean }) {
  const pathname = usePathname();

  const renderLink = (item: { href: string; label: string; icon: string }) => {
    const active = pathname === item.href || pathname.startsWith(item.href + "/");
    return (
      <Link
        key={item.href}
        href={item.href}
        className={`group flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-semibold transition-all duration-150 ${
          active
            ? "bg-gradient-to-r from-indigo-500/15 via-violet-500/10 to-transparent text-ink shadow-[inset_2px_0_0] shadow-indigo-500"
            : "text-ink-soft hover:bg-surface-2 hover:text-ink"
        }`}
      >
        <span
          className={`text-base transition-transform duration-150 ${
            active ? "scale-110" : "group-hover:scale-110"
          }`}
        >
          {item.icon}
        </span>
        {item.label}
        {active && (
          <span className="ml-auto h-1.5 w-1.5 rounded-full bg-gradient-to-r from-indigo-500 to-fuchsia-500" />
        )}
      </Link>
    );
  };

  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-line bg-surface px-4 py-6 md:flex">
      <Link href="/dashboard" className="px-2">
        <LogoWordmark />
      </Link>
      <nav className="mt-8 flex flex-1 flex-col gap-1">
        {NAV.map(renderLink)}
        {isAdmin && (
          <>
            <div className="mt-6 mb-2 px-3.5 text-[10px] font-bold uppercase tracking-widest text-ink-faint">
              Platform
            </div>
            {ADMIN_NAV.map(renderLink)}
          </>
        )}
      </nav>
      <div className="card mx-1 bg-gradient-to-br from-indigo-500/10 via-violet-500/10 to-fuchsia-500/10 p-4">
        <p className="text-xs font-bold">Need more power?</p>
        <p className="mt-1 text-xs text-ink-soft">
          Upgrade for more automations and daily uploads.
        </p>
        <Link href="/billing" className="btn-primary mt-3 w-full !py-2 text-xs">
          View plans
        </Link>
      </div>
    </aside>
  );
}
