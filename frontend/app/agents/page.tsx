"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";
import { ActionButton, Card, StatusPill } from "../../components/primitives";

type Agent = {
  id: string;
  company: string;
  routes: string[];
  services: string[];
  capabilities: string[];
  contact: string;
  status: string;
};

const split = (s: string) => s.split(",").map((x) => x.trim()).filter(Boolean);

export default function Agents() {
  const [rows, setRows] = useState<Agent[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ company: "", routes: "", services: "", capabilities: "", contact: "" });

  const refresh = useCallback(async () => {
    setError("");
    try {
      setRows(await api<Agent[]>("/agents"));
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
      await api("/agents", {
        method: "POST",
        body: JSON.stringify({
          company: form.company,
          routes: split(form.routes),
          services: split(form.services),
          capabilities: split(form.capabilities),
          contact: form.contact,
        }),
      });
      setNotice(`Agent ${form.company} added ✓`);
      setForm({ company: "", routes: "", services: "", capabilities: "", contact: "" });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  return (
    <>
      <Card title="Add agent">
        {error ? <p className="pill red">{error}</p> : null}
        {notice ? <p className="pill green">{notice}</p> : null}
        <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <input aria-label="Company" placeholder="Company" value={form.company} onChange={set("company")} />
          <input aria-label="Routes" placeholder="Routes (comma separated, e.g. China>Lagos)" value={form.routes} onChange={set("routes")} />
          <input aria-label="Services" placeholder="Services (e.g. ocean, air)" value={form.services} onChange={set("services")} />
          <input aria-label="Capabilities" placeholder="Capabilities (e.g. 20ft, cartons)" value={form.capabilities} onChange={set("capabilities")} />
          <input aria-label="Contact" placeholder="Contact" value={form.contact} onChange={set("contact")} />
          <p>
            <ActionButton busy={busy}>Add agent</ActionButton>
          </p>
        </form>
      </Card>
      <Card title={`Agents (${rows.length})`}>
        {rows.length === 0 && !error ? <p className="muted">No agents yet — add your first above.</p> : null}
        {rows.map((a) => (
          <div key={a.id} className="card" style={{ marginBottom: 10 }}>
            <p>
              <b>{a.company}</b> <StatusPill tone={a.status === "Active" ? "green" : "red"}>{a.status}</StatusPill>
            </p>
            <p className="muted">
              Routes: {a.routes.join(", ") || "—"} · Services: {a.services.join(", ") || "—"} · Capabilities:{" "}
              {a.capabilities.join(", ") || "—"}
              {a.contact ? ` · ${a.contact}` : ""}
            </p>
          </div>
        ))}
      </Card>
    </>
  );
}
