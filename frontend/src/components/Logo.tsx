export function LogoMark({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none" aria-hidden>
      <defs>
        <linearGradient id="lp-grad" x1="0" y1="0" x2="40" y2="40">
          <stop offset="0%" stopColor="#6366f1" />
          <stop offset="55%" stopColor="#8b5cf6" />
          <stop offset="100%" stopColor="#d946ef" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="36" height="36" rx="11" fill="url(#lp-grad)" />
      <path
        d="M14 12.5v15l13-7.5-13-7.5z"
        fill="white"
        fillOpacity="0.95"
      />
      <circle cx="29.5" cy="11" r="4.5" fill="white" fillOpacity="0.35" />
    </svg>
  );
}

export function LogoWordmark({ size = 28 }: { size?: number }) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <LogoMark size={size} />
      <span className="font-display text-lg font-bold tracking-tight">
        Logo<span className="gradient-text">Pilot</span>
      </span>
    </span>
  );
}
