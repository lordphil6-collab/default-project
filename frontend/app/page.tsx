"use client";
import { useCallback, useEffect, useState } from "react";
import { api, Situation, TodayCounts } from "../lib/api";
import { ActionButton, Card, StatusPill } from "../components/primitives";

export default function Home() {
  const [counts, setCounts] = useState<TodayCounts | null>(null);
  const [situations, setSituations] = useState<Situation[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [customer, setCustomer] = useState("");
  const [channel, setChannel] = useState("email");
  const [body, setBody] = useState("");
  const [sending, setSending] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [c, s] = await Promise.all([api<TodayCounts>("/dashboard/today"), api<Situation[]>("/situations")]);
      setCounts(c);
      setSituations(s);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSending(true);
    setError("");
    try {
      await api("/intake", {
        method: "POST",
        body: JSON.stringify({ customer_name: customer, channel, body }),
      });
      setCustomer("");
      setBody("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Send failed");
    } finally {
      setSending(false);
    }
  }

  return (
    <>
      <Card title="Today — What needs attention?">
        {loading && !counts ? (
          <p className="muted">Loading live data…</p>
        ) : counts ? (
          <p>
            <StatusPill tone="red">{counts.urgent} Urgent</StatusPill>{" "}
            <StatusPill tone="amber">{counts.follow_ups} Follow-ups</StatusPill>{" "}
            <StatusPill tone="indigo">{counts.pending_agents} Pending agents</StatusPill>{" "}
            <StatusPill tone="amber">{counts.awaiting_approval} Awaiting approval</StatusPill>{" "}
            <StatusPill tone="red">{counts.exceptions} Exceptions</StatusPill>
          </p>
        ) : null}
        {error ? <p className="pill red">{error}</p> : null}
      </Card>

      <Card title="New enquiry">
        <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <input aria-label="Customer name" placeholder="Customer company" value={customer} onChange={(e) => setCustomer(e.target.value)} />
          <select aria-label="Channel" value={channel} onChange={(e) => setChannel(e.target.value)}>
            <option value="email">Email</option>
            <option value="whatsapp">WhatsApp</option>
          </select>
          <textarea aria-label="Enquiry text" rows={3} placeholder="e.g. quote for 5 cartons from Guangzhou to Lagos" value={body} onChange={(e) => setBody(e.target.value)} />
          <p>
            <ActionButton> {sending ? "Sending…" : "Capture enquiry"} </ActionButton>
          </p>
        </form>
      </Card>

      <Card title={`Situations (${situations.length})`}>
        {loading && situations.length === 0 ? (
          <p className="muted">Loading…</p>
        ) : situations.length === 0 && !error ? (
          <p className="muted">No situations yet — capture an enquiry above and it appears here.</p>
        ) : (
          situations.map((s) => (
            <div key={s.id} className="card" style={{ marginBottom: 10 }}>
              <p>
                <b className="mono">{s.id.slice(0, 8)}</b> <StatusPill tone="amber">{s.status}</StatusPill>
              </p>
              {s.missing.length > 0 ? <p className="muted">Missing: {s.missing.join(", ")}</p> : null}
              {s.next_action ? <p className="muted">Next: {s.next_action}</p> : null}
            </div>
          ))
        )}
      </Card>
    </>
  );
}
