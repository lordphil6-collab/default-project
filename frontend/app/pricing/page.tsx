"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";
import { ActionButton, Card, StatusPill } from "../../components/primitives";

type Rule = { id: string; name: string; kind: string; value: number; min_margin: number };

export default function Pricing() {
  const [rows, setRows] = useState<Rule[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ name: "Standard", kind: "percent", value: "12", min_margin: "0" });

  const refresh = useCallback(async () => {
    setError("");
    try {
      setRows(await api<Rule[]>("/markup-rules"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
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
      await api("/markup-rules", {
        method: "POST",
        body: JSON.stringify({ ...form, value: Number(form.value) || 0, min_margin: Number(form.min_margin) || 0 }),
      });
      setNotice(`Rule ${form.name} saved ✓ (Manager+ only)`);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Card title="New markup rule">
        {error ? <p className="pill red">{error}</p> : null}
        {notice ? <p className="pill green">{notice}</p> : null}
        <form onSubmit={submit} style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <input aria-label="Rule name" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
          <select aria-label="Kind" value={form.kind} onChange={(e) => setForm((f) => ({ ...f, kind: e.target.value }))}>
            <option value="percent">percent %</option>
            <option value="fixed">fixed $</option>
            <option value="minimum">minimum %</option>
            <option value="combined">combined</option>
          </select>
          <input aria-label="Value" style={{ width: 90 }} value={form.value} onChange={(e) => setForm((f) => ({ ...f, value: e.target.value }))} />
          <ActionButton busy={busy}>Save rule</ActionButton>
        </form>
      </Card>
      <Card title={`Rules (${rows.length})`}>
        {rows.map((r) => (
          <p key={r.id} className="muted">
            <b>{r.name}</b> — {r.kind} {r.value}
            {r.kind.startsWith("archived") ? <StatusPill tone="red">archived</StatusPill> : null}
          </p>
        ))}
      </Card>
    </>
  );
}
