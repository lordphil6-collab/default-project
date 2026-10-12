"use client";
import { useEffect, useState } from "react";
import { StatusPill } from "./primitives";

type BillingStatus = { status: string; trial_ends: string | null };

function daysLeft(iso: string): number {
  return Math.max(0, Math.ceil((new Date(iso).getTime() - Date.now()) / 86_400_000));
}

/** Trial/entitlement pill with days-left and an upgrade nudge when expiring. */
export function TrialPill() {
  const [billing, setBilling] = useState<BillingStatus | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch("/api/auth/get-session");
        const sess = (await res.json()) as { session?: object | null };
        if (!sess.session) return; // logged out — stay quiet
        const tok = await fetch("/api/auth/token");
        if (!tok.ok) return;
        const { token } = (await tok.json()) as { token?: string };
        if (!token) return;
        const s = await fetch("/api/auth/get-session");
        const orgId = ((await s.json()) as { session?: { activeOrganizationId?: string } | null })
          ?.session?.activeOrganizationId;
        if (!orgId) return;
        const r = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/billing/status`,
          { headers: { Authorization: `Bearer ${token}`, "X-Org-Id": orgId, "X-Role": "CSR" } }
        );
        if (r.ok) setBilling(await r.json());
      } catch {
        // Billing unreachable — keep the neutral pill, never break the topbar.
      }
    })();
  }, []);

  if (!billing) return <StatusPill tone="indigo">Trial</StatusPill>;
  if (billing.status === "active") return <StatusPill tone="green">Active</StatusPill>;
  const left = billing.trial_ends ? daysLeft(billing.trial_ends) : null;
  return (
    <a href="/billing" style={{ textDecoration: "none" }} title="Open billing">
      <StatusPill tone={left !== null && left <= 7 ? "amber" : "indigo"}>
        {left === null ? billing.status : `${left}d left`}
      </StatusPill>
    </a>
  );
}
