"use client";

const PLANS = [
  {
    name: "Trial",
    price: "Free",
    period: "3 days",
    gradient: "from-slate-500 to-slate-700",
    features: ["3 automations", "1 Instagram account", "20 uploads / day", "Standard queue"],
  },
  {
    name: "Starter",
    price: "$19.99",
    period: "/ month",
    gradient: "from-indigo-500 to-violet-600",
    popular: true,
    features: ["20 automations", "3 Instagram accounts", "100 uploads / day", "250 queue capacity"],
  },
  {
    name: "Pro",
    price: "$35.99",
    period: "/ month",
    gradient: "from-fuchsia-500 to-pink-600",
    features: ["100 automations", "10 Instagram accounts", "500 uploads / day", "500 queue capacity"],
  },
];

export default function BillingPage() {
  return (
    <div className="space-y-8">
      <p className="text-sm text-ink-soft">
        Pay by card (Stripe) or crypto. Plan changes apply instantly.
      </p>

      <div className="grid gap-6 md:grid-cols-3">
        {PLANS.map((p) => (
          <div
            key={p.name}
            className={`card relative p-6 transition hover:-translate-y-1 ${
              p.popular ? "ring-2 ring-indigo-500/60" : ""
            }`}
          >
            {p.popular && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-indigo-500 to-fuchsia-500 px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-white shadow">
                Most popular
              </span>
            )}
            <div
              className={`inline-flex rounded-xl bg-gradient-to-br ${p.gradient} px-3 py-1.5 text-xs font-bold text-white shadow`}
            >
              {p.name}
            </div>
            <div className="mt-5 flex items-baseline gap-1.5">
              <span className="font-display text-4xl font-bold">{p.price}</span>
              <span className="text-sm text-ink-faint">{p.period}</span>
            </div>
            <ul className="mt-6 space-y-2.5 text-sm text-ink-soft">
              {p.features.map((f) => (
                <li key={f} className="flex items-center gap-2.5">
                  <span className="flex h-4 w-4 items-center justify-center rounded-full bg-emerald-500/15 text-[9px] font-bold text-emerald-500">
                    ✓
                  </span>
                  {f}
                </li>
              ))}
            </ul>
            <button
              disabled
              title="Payments are being configured"
              className={`mt-8 w-full rounded-xl py-2.5 text-sm font-bold text-white transition bg-gradient-to-r ${p.gradient} opacity-60 cursor-not-allowed`}
            >
              Coming soon
            </button>
          </div>
        ))}
      </div>

      <div className="card flex items-center gap-4 p-5">
        <span className="text-2xl">🪙</span>
        <div>
          <p className="text-sm font-bold">Crypto payments supported</p>
          <p className="text-xs text-ink-soft">
            Pay with USDT, BTC and more via Cryptomus / MaxelPay once billing goes live.
          </p>
        </div>
      </div>
    </div>
  );
}
