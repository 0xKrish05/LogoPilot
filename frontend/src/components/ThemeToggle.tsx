"use client";

import { useTheme } from "@/lib/theme";

export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  return (
    <button
      onClick={toggle}
      aria-label="Toggle theme"
      className="relative inline-flex h-9 w-16 items-center rounded-full border border-line bg-surface-2 transition-colors hover:border-brand-300"
    >
      <span
        className={`absolute flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br text-sm shadow-md transition-all duration-300 ${
          theme === "dark"
            ? "left-8 from-indigo-500 to-violet-600"
            : "left-1 from-amber-300 to-orange-400"
        }`}
      >
        {theme === "dark" ? "🌙" : "☀️"}
      </span>
    </button>
  );
}
