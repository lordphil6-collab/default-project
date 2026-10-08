"use client";
import { useState } from "react";
import { api } from "../../lib/api";
import { ActionButton, Card, StatusPill } from "../../components/primitives";

type Option = { agent: string; trips: number; low: number; avg: number; high: number; transit_days: number | null };
type Guideline = {
  available: boolean; basis: string; confidence: string; low?: number; typical?: number; high?: number;
  count?: number; options?: Option[]; note?: string;
};
type Match = { agent_id: string; agent: string; score: number; reasons: string[] };

export default function Quote() {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [load, setLoad] = useState("");
  const [goods, setGoods] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [guide, setGuide] = useState<Guideline | null>(null);
  const [matched, setMatched] = useState<Match[]>([]);
  const [sid, setSid] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setGuide(null);
    setMatched([]);
    setSid(null);
    try {
      const body = `Quote request from ${origin} to ${destination}. Load: ${load}. Goods: ${goods}`.trim();
      const sit = await api<{ id: string }>("/intake", {
        method: "POST",
        body: JSON.stringify({ customer_name: "Self quote", channel: "web", body }),
      });
      setSid(sit.id);
      const [g, m] = await Promise.all([
        api<Guideline>(`/situations/${sit.id}/guideline`),
        api<Match[]>(`/agents/match?situation_id=${sit.id}`),
      ]);
      setGuide(g);
      setMatched(m);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed — sign in first.");
    } finally {
      setBusy(false);
    }
  }

  const input = (label: string, value: string, set: (v: string) => void, ph: string) => (
    <input aria-label={label} placeholder={ph} value={value} onChange={(e) => set(e.target.value)} />
  );

  return (
    <>
      <div className="card">
        <h2 style={{ fontSize: 16, margin: "4px 0 8px" }}>Search freight rates</h2>
        <p className="muted">Account required — results come from your carriers plus live history.</p>
        {error ? <p className="pill red">{error}</p> : null}
        <form onSubmit={submit} style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {input("Origin", origin, setOrigin, "Where from?")}
          {input("Destination", destination, setDestination, "Where to?")}
          {input("Load", load, setLoad, "e.g. 1×20ft, 200kg air")}
          {input("Goods", goods, setGoods, "What goods?")}
          <button className="btn" type="submit" disabled={busy} style={busy ? { opacity: 0.6 } : undefined}>
            Search rates{busy ? " …" : ""}
          </button>
        </form>
      </div>

      {guide ? (
        <Card title="Instant estimate">
          {guide.available ? (
            <p>
              <b className="mono">${guide.low?.toLocaleString()} – ${guide.high?.toLocaleString()}</b>{" "}
              (typical <b className="mono">${guide.typical?.toLocaleString()}</b>){" "}
              <StatusPill tone={guide.confidence === "High" ? "green" : "amber"}>{guide.confidence}</StatusPill>
              <span className="muted"> · {guide.basis} · {guide.count} quote(s)</span>
            </p>
          ) : (
            <p className="muted">{guide.note}</p>
          )}
          {sid ? <p><a href={`/situations/${sid}`}>Open as situation →</a></p> : null}
        </Card>
      ) : null}

      {guide?.options && guide.options.length > 0 ? (
        <Card title={`Carrier options (${guide.options.length}) — from rate history`}>
          <table className="cmp">
            <thead>
              <tr>
                <th>Carrier</th>
                <th>Avg all-in</th>
                <th>Range</th>
                <th>Trips</th>
                <th>Transit</th>
              </tr>
            </thead>
            <tbody>
              {guide.options.map((o, i) => (
                <tr key={o.agent}>
                  <td>
                    {i === 0 ? <StatusPill tone="green">cheapest</StatusPill> : null} {o.agent}
                  </td>
                  <td className="mono">${o.avg.toLocaleString()}</td>
                  <td className="mono">${o.low.toLocaleString()} – ${o.high.toLocaleString()}</td>
                  <td>{o.trips}</td>
                  <td>{o.transit_days ? `${o.transit_days}d` : "?"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}

      {matched.length > 0 ? (
        <Card title="Recommended for this shipment">
          {matched.map((m) => (
            <p key={m.agent_id} className="muted">
              <b>{m.agent}</b> — score {m.score}: {m.reasons.join("; ")}
            </p>
          ))}
        </Card>
      ) : null}
    </>
  );
}
