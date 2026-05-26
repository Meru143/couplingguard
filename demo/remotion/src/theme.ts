// Single source of truth for colors / typography so every scene stays
// on-brand without duplicating literals.

export const COLORS = {
  bgFrom: "#0f172a",
  bgTo: "#1e1b4b",
  fg: "#f8fafc",
  fgDim: "#cbd5e1",
  fgMute: "#94a3b8",
  fgFaint: "#64748b",
  card: "#1e293b",
  cardStroke: "#334155",
  prCard: "#0d1117",
  prCardStroke: "#30363d",
  prFg: "#e6edf3",
  prFgDim: "#7d8590",
  link: "#58a6ff",
  riskLow: "#22c55e",
  riskMid: "#f59e0b",
  riskHigh: "#ef4444",
  accent: "#f59e0b",
} as const;

export const FONTS = {
  sans:
    "-apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, 'Helvetica Neue', Arial, sans-serif",
  mono:
    "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace",
} as const;
