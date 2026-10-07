"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";
import { ActionButton, Card, StatusPill } from "../../components/primitives";

type Plan = { id: string; name: string; monthly_price: number };
type Status = { status: string; trial_ends: string | null; providers: { stripe: boolean; paystack: boolean } };

export default function Billing() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [status, setStatus] = useState<Status | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setError("");
    try {
      const [p, s] = await Promise.all([api<Plan[]>("/billing/plans"), api<Status>("/billing/status")]);
      setPlans(p);
      setStatus(s);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function subscribe(plan: Plan) {
    setBusy(plan.id);
    setError("");
    try {
      const r = await api<{ provider: string; url: string }>("/billing/checkout", {
        method: "POST",
        body: JSON.stringify({ plan_id: plan.id }),
      });
      window.location.href = r.url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <Card title="Subscription">
        {error ? <p className="pill red">{error}</p> : null}
        {status ? (
          <p>
            Status: <StatusPill tone={status.status === "active" ? "green" : "amber"}>{status.status}</StatusPill>{" "}
            {status.trial_ends ? <span className="muted">trial ends {status.trial_ends.slice(0, 10)}</span> : null}
          </p>
        ) : (
          <p className="muted">Loading…</p>
        )}
        <p className="muted">
          Providers: Stripe {status?.providers.stripe ? "on" : "off"} · Paystack {status?.providers.paystack ? "on" : "off"}.
          Owner role required to subscribe.
        </p>
      </Card>
      <Card title={`Plans (${plans.length})`}>
        {plans.map((p) => (
          <p key={p.id}>
            <b>{p.name}</b> <span className="mono">${p.monthly_price}/mo</span>{" "}
            <ActionButton busy={busy === p.id} secondary onClick={() => subscribe(p)}>
              Subscribe
            </ActionButton>
          </p>
        ))}
      </Card>
    </>
  );
}
