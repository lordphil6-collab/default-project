"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";
import { ActionButton, Card, StatusPill } from "../../components/primitives";

type Org = { org_id: string; name: string; trial_ends: string | null; entitlement: string; plan_id: string | null };
type Audit = { actor: string; action: string; detail: Record<string, unknown>; org_id: string; at: string | null };

export default function Admin() {
  const [orgs, setOrgs] = useState<Org[]>([]);
  const [audit, setAudit] = useState<Audit[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ org_id: "", status: "active" });

  const refresh = useCallback(async () => {
    setError("");
    try {
      const [o, a] = await Promise.all([api<Org[]>("/admin/orgs"), api<Audit[]>("/admin/audit?limit=100")]);
      setOrgs(o);
      setAudit(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed (Owner role required)");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const r = await api<{ org_id: string; status: string }>("/admin/entitlements", {
        method: "POST",
        body: JSON.stringify(form),
      });
      setNotice(`Entitlement set: ${r.org_id.slice(0, 8)} → ${r.status} ✓`);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Card title="Organizations & trials">
        {error ? <p className="pill red">{error}</p> : null}
        {notice ? <p className="pill green">{notice}</p> : null}
        {orgs.map((o) => (
          <p key={o.org_id} className="muted">
            <b>{o.name}</b> <span className="mono">{o.org_id.slice(0, 8)}</span>{" "}
            <StatusPill tone={o.entitlement === "active" ? "green" : "amber"}>{o.entitlement}</StatusPill>{" "}
            trial ends {o.trial_ends ? o.trial_ends.slice(0, 10) : "—"}
          </p>
        ))}
        <form onSubmit={submit} style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
          <input aria-label="Org id" placeholder="org id (8 chars)" style={{ width: 200 }} value={form.org_id} onChange={(e) => {
            const v = e.target.value;
            const full = orgs.find((o) => o.org_id.startsWith(v))?.org_id || v;
            setForm((f) => ({ ...f, org_id: full }));
          }} />
          <select aria-label="Status" value={form.status} onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}>
            <option value="trialing">trialing</option>
            <option value="active">active</option>
            <option value="past_due">past_due</option>
            <option value="cancelled">cancelled</option>
          </select>
          <ActionButton busy={busy} submit>Set entitlement</ActionButton>
        </form>
      </Card>
      <Card title={`Audit trail (${audit.length})`}>
        {audit.map((a, i) => (
          <p key={i} className="muted">
            {a.at ? a.at.slice(0, 19).replace("T", " ") : "?"} — <b>{a.action}</b> by {a.actor} <span className="mono">[{a.org_id.slice(0, 8)}]</span>
          </p>
        ))}
      </Card>
    </>
  );
}
