import Link from "next/link";
import { LogoWordmark } from "@/components/Logo";

const FEATURES = [
  {
    icon: "🎯",
    title: "Smart filtering",
    body: "Reels are checked for duration, duplicates and queue capacity before they ever enter your pipeline.",
  },
  {
    icon: "🎨",
    title: "Automatic logo overlay",
    body: "Eight positions, chroma key, opacity and animated logos — applied frame-perfect by FFmpeg.",
  },
  {
    icon: "📅",
    title: "Human-like scheduling",
    body: "Posts are spaced through your day with night-mode quiet hours, so your account looks natural.",
  },
  {
    icon: "🚀",
    title: "Upload & submit",
    body: "Branded reels go straight to your Instagram Business account and on to Clipster — hands-free.",
  },
  {
    icon: "📊",
    title: "Live pipeline view",
    body: "Watch every reel move through download, edit, upload and submit in real time.",
  },
  {
    icon: "🔐",
    title: "Secure by design",
    body: "Google sign-in, encrypted credentials and aggressive temp-file cleanup after every job.",
  },
];

const PLANS = [
  {
    name: "Trial",
    price: "Free",
    period: "3 days",
    features: ["3 automations", "1 Instagram account", "20 uploads / day"],
    highlight: false,
  },
  {
    name: "Starter",
    price: "$19.99",
    period: "per month",
    features: ["20 automations", "3 Instagram accounts", "100 uploads / day", "250 queue capacity"],
    highlight: true,
  },
  {
    name: "Pro",
    price: "$35.99",
    period: "per month",
    features: ["100 automations", "10 Instagram accounts", "500 uploads / day", "500 queue capacity"],
    highlight: false,
  },
];

export default function Landing() {
  return (
    <main className="min-h-screen bg-white text-slate-900">
      {/* Nav */}
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <LogoWordmark />
        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="rounded-xl px-4 py-2 text-sm font-semibold text-slate-600 hover:text-slate-900"
          >
            Sign in
          </Link>
          <Link href="/login" className="btn-primary !py-2 text-sm">
            Get started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="mx-auto max-w-4xl px-6 pt-20 pb-24 text-center">
        <span className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-4 py-1.5 text-xs font-semibold text-slate-600">
          <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-emerald-500" />
          Automated reel promotion, end to end
        </span>
        <h1 className="mx-auto mt-8 max-w-3xl font-display text-5xl font-bold leading-[1.1] tracking-tight sm:text-6xl">
          Your logo on every reel.{" "}
          <span className="gradient-text">On autopilot.</span>
        </h1>
        <p className="mx-auto mt-6 max-w-xl text-lg leading-relaxed text-slate-500">
          Paste reel links. LogoPilot brands them with your logo, posts them to
          your Instagram on a natural schedule, and submits them to Clipster —
          while you sleep.
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <Link href="/login" className="btn-primary !px-8 !py-3.5 text-base">
            Start free trial
          </Link>
          <a
            href="#how"
            className="btn-ghost !border-slate-200 !bg-white !px-8 !py-3.5 text-base !text-slate-600 hover:!bg-slate-50"
          >
            See how it works
          </a>
        </div>

        {/* Pipeline strip */}
        <div className="mx-auto mt-20 flex max-w-2xl flex-wrap items-center justify-center gap-2 text-xs font-semibold text-slate-400">
          {["Collect", "Filter", "Schedule", "Download", "Brand", "Upload", "Submit"].map(
            (step, i, arr) => (
              <span key={step} className="flex items-center gap-2">
                <span className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-slate-600 shadow-sm">
                  {step}
                </span>
                {i < arr.length - 1 && <span className="text-slate-300">→</span>}
              </span>
            )
          )}
        </div>
      </section>

      {/* Features */}
      <section id="how" className="border-t border-slate-100 bg-slate-50/60 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="text-center font-display text-3xl font-bold tracking-tight">
            Everything between “found a reel” and “it’s live”
          </h2>
          <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
              >
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500/10 to-fuchsia-500/10 text-xl">
                  {f.icon}
                </div>
                <h3 className="mt-4 font-display text-base font-bold">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-500">{f.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-24">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="text-center font-display text-3xl font-bold tracking-tight">
            Simple pricing
          </h2>
          <p className="mt-3 text-center text-slate-500">
            Start free. Upgrade when your pipeline does.
          </p>
          <div className="mt-14 grid gap-6 md:grid-cols-3">
            {PLANS.map((p) => (
              <div
                key={p.name}
                className={`relative rounded-2xl border p-7 ${
                  p.highlight
                    ? "border-transparent bg-gradient-to-b from-indigo-500 via-violet-600 to-fuchsia-600 text-white shadow-xl shadow-indigo-500/25"
                    : "border-slate-200 bg-white"
                }`}
              >
                {p.highlight && (
                  <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-white px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-indigo-600 shadow">
                    Most popular
                  </span>
                )}
                <h3 className="font-display text-lg font-bold">{p.name}</h3>
                <div className="mt-4 flex items-baseline gap-2">
                  <span className="font-display text-4xl font-bold">{p.price}</span>
                  <span className={p.highlight ? "text-white/70" : "text-slate-400"}>
                    {p.period}
                  </span>
                </div>
                <ul className="mt-6 space-y-2.5 text-sm">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-center gap-2.5">
                      <span
                        className={`flex h-4 w-4 items-center justify-center rounded-full text-[9px] font-bold ${
                          p.highlight ? "bg-white/20" : "bg-emerald-500/15 text-emerald-600"
                        }`}
                      >
                        ✓
                      </span>
                      {f}
                    </li>
                  ))}
                </ul>
                <Link
                  href="/login"
                  className={`mt-8 block rounded-xl py-2.5 text-center text-sm font-semibold transition ${
                    p.highlight
                      ? "bg-white text-indigo-600 hover:bg-indigo-50"
                      : "border border-slate-200 text-slate-700 hover:bg-slate-50"
                  }`}
                >
                  {p.name === "Trial" ? "Start free" : `Choose ${p.name}`}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="border-t border-slate-100 py-10 text-center text-sm text-slate-400">
        © {new Date().getFullYear()} LogoPilot. Built for creators who automate.
      </footer>
    </main>
  );
}
