interface StatCardProps {
  label: string;
  value: string | number;
  hint?: string;
  icon: React.ReactNode;
  accent: "indigo" | "emerald" | "amber" | "fuchsia" | "sky" | "rose";
}

const ACCENTS = {
  indigo: "from-indigo-500 to-violet-600 shadow-indigo-500/30",
  emerald: "from-emerald-500 to-teal-600 shadow-emerald-500/30",
  amber: "from-amber-400 to-orange-500 shadow-amber-500/30",
  fuchsia: "from-fuchsia-500 to-pink-600 shadow-fuchsia-500/30",
  sky: "from-sky-400 to-cyan-600 shadow-sky-500/30",
  rose: "from-rose-500 to-red-600 shadow-rose-500/30",
};

export function StatCard({ label, value, hint, icon, accent }: StatCardProps) {
  return (
    <div className="card group p-5 transition-transform duration-200 hover:-translate-y-0.5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-ink-faint">
            {label}
          </p>
          <p className="mt-2 font-display text-3xl font-bold tabular-nums">
            {value}
          </p>
          {hint && <p className="mt-1 text-xs text-ink-faint">{hint}</p>}
        </div>
        <div
          className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br text-xl text-white shadow-lg ${ACCENTS[accent]}`}
        >
          {icon}
        </div>
      </div>
    </div>
  );
}
