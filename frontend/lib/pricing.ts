// Phase 6 pricing preview — must match backend/app/services/pricing.py exactly.
export function applyMarkupPreview(agentTotal: number, kind: string, value: number, minMargin = 0): {
  agentTotal: number; markupAmount: number; finalPrice: number;
} {
  const r2 = (n: number) => Math.round(n * 100) / 100;
  let markup: number;
  if (kind === "percent") markup = agentTotal * (value / 100);
  else if (kind === "fixed") markup = value;
  else if (kind === "minimum") markup = Math.max(agentTotal * (value / 100), minMargin);
  else if (kind === "combined") markup = agentTotal * (value / 100) + minMargin;
  else throw new Error(`unknown markup kind: ${kind}`);
  if (kind !== "combined") markup = Math.max(markup, minMargin);
  markup = r2(markup);
  return { agentTotal: r2(agentTotal), markupAmount: markup, finalPrice: r2(agentTotal + markup) };
}
