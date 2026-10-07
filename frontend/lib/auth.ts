// Phase 2 Better Auth wiring stub — real session UI lands with login (Phase 4+).
// Contract: browser sends Authorization Bearer JWT + X-Org-Id + X-Role;
// FastAPI enforces org scoping (backend/app/auth.py). No secrets here.

export type Role = "CSR" | "Sales" | "Ops" | "Manager" | "Owner";

export function authHeaders(opts: { token: string; orgId: string; role?: Role }): Record<string, string> {
  return {
    Authorization: `Bearer ${opts.token}`,
    "X-Org-Id": opts.orgId,
    "X-Role": opts.role ?? "CSR",
  };
}

export function trialDaysLeft(trialEndsIso: string, nowMs = Date.now()): number {
  const ms = new Date(trialEndsIso).getTime() - nowMs;
  return Math.max(0, Math.ceil(ms / 86_400_000));
}

export function canWrite(entitlement: string): boolean {
  return entitlement === "trialing" || entitlement === "active";
}
