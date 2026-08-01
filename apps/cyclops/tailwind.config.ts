import type { Config } from "tailwindcss";

/**
 * The colour tokens mirror the validated data-viz palette so the app chrome
 * and any charts stay one system. Ink and surface roles are named by job
 * rather than by hue, so the dark variants swap in one place.
 */
const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "var(--surface-1)",
          raised: "var(--surface-2)",
          sunken: "var(--surface-0)",
        },
        ink: {
          DEFAULT: "var(--text-primary)",
          secondary: "var(--text-secondary)",
          muted: "var(--text-muted)",
        },
        line: {
          DEFAULT: "var(--border)",
          strong: "var(--border-strong)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          soft: "var(--accent-soft)",
          ink: "var(--accent-ink)",
        },
        good: "var(--good)",
        warn: "var(--warn)",
        bad: "var(--bad)",
      },
      fontFamily: {
        sans: ["system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Consolas", "monospace"],
      },
      borderRadius: {
        card: "10px",
      },
    },
  },
  plugins: [],
};

export default config;
