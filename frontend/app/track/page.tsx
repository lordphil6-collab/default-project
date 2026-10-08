"use client";
import { useEffect, useState } from "react";
import { Card, StatusPill } from "../../components/primitives";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Track = {
  reference: string;
  route: string;
  status: string;
  outcome: string | null;
  price: { total: number; currency: string; validity_days: number } | null;
  missing: string[];
};

const STAGES = ["New", "RFQ In Progress", "Quotation Received", "Quote Sent", "Accepted"];

export default function Track() {
  const [token, setToken] = useState("");
  const [data, setData] = useState<Track | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const m = /[?&]token=([^&]+)/.exec(window.location.search);
    if (m) {
      setToken(decodeURIComponent(m[1]));
    }
  }, []);

  async function lookup(t: string) {
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${API}/public/track/${encodeURIComponent(t)}`);
      if (!res.ok) throw new Error("Reference not found — check the link from your forwarder.");
      setData(await res.json());
    } catch (err) {
      setData(null);
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  const stageIdx = (s: string) => {
    if (s === "Accepted") return 4;
    const i = STAGES.indexOf(s);
    return i < 0 ? 0 : Math.min(i, 3);
  };

  return (
    <div className="card" style={{ maxWidth: 560 }}>
      <h2 style={{ fontSize: 16, margin: "4px 0 8px" }}>Track your shipment</h2>
      {error ? <p className="pill red">{error}</p> : null}
      <div style={{ display: "flex", gap: 8 }}>
        <input aria-label="Tracking reference" placeholder="paste your tracking link token" style={{ flex: 1 }} value={token} onChange={(e) => setToken(e.target.value)} />
        <button className="btn" type="button" disabled={busy} onClick={() => lookup(token.trim())}>
          Track{busy ? " …" : ""}
        </button>
      </div>
      {data ? (
        <>
          <p>
            <b>{data.route}</b> <StatusPill tone={data.outcome === "Accepted" ? "green" : "amber"}>{data.outcome || data.status}</StatusPill>
          </p>
          <div className="timeline">
            {STAGES.map((s, i) => (
              <div key={s} style={{ opacity: i <= stageIdx(data.outcome || data.status) ? 1 : 0.4 }}>
                {i <= stageIdx(data.outcome || data.status) ? "●" : "○"} {s}
              </div>
            ))}
          </div>
          {data.price ? (
            <p>
              Quoted: <b className="mono">{data.price.currency} {data.price.total.toLocaleString()}</b>{" "}
              <span className="muted">valid {data.price.validity_days} days</span>
            </p>
          ) : (
            <p className="muted">Quotation in progress — check back soon.</p>
          )}
          <p className="muted">Reference {data.reference}</p>
        </>
      ) : null}
    </div>
  );
}
