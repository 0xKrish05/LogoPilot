"use client";

import { motion } from "framer-motion";

interface Orb {
  size: number;
  className: string;
  x: number[];
  y: number[];
  duration: number;
  delay?: number;
}

const ORBS: Orb[] = [
  { size: 320, className: "bg-indigo-400/30 dark:bg-indigo-500/20 -left-20 -top-32", x: [0, 40, 0], y: [0, 30, 0], duration: 18 },
  { size: 280, className: "bg-fuchsia-400/30 dark:bg-fuchsia-500/20 right-[-6rem] top-10", x: [0, -30, 0], y: [0, 40, 0], duration: 22, delay: 1 },
  { size: 240, className: "bg-sky-400/25 dark:bg-sky-500/15 left-1/3 top-1/2", x: [0, 25, -25, 0], y: [0, -20, 20, 0], duration: 26, delay: 2 },
  { size: 200, className: "bg-emerald-400/20 dark:bg-emerald-500/10 right-1/4 bottom-0", x: [0, -20, 0], y: [0, -30, 0], duration: 20, delay: 0.5 },
];

/**
 * Decorative blurred gradient blobs that drift slowly behind page content.
 * Purely visual — `pointer-events-none` and `aria-hidden`.
 */
export function FloatingOrbs({ className = "" }: { className?: string }) {
  return (
    <div className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`} aria-hidden>
      {ORBS.map((orb, i) => (
        <motion.div
          key={i}
          className={`absolute rounded-full blur-3xl ${orb.className}`}
          style={{ width: orb.size, height: orb.size }}
          animate={{ x: orb.x, y: orb.y }}
          transition={{
            duration: orb.duration,
            delay: orb.delay ?? 0,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
}
