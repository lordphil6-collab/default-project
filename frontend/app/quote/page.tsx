"use client";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Quote() {
  const [name, setName] = useState("");
  const [contact, setContact] = useState("");
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [details, setDetails] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState<{ reference: string; summary: string; missing: string[] } | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const body = `Quote request from ${origin} to ${destination}. ${details}`.trim();
      const res = await fetch(`${API}/public/enquiries`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ customer_name: name, contact, body }),
      });
      if (!res.ok) throw new Error(`${res.status}: ${(await res.text()).slice(0, 200)}`);
      setDone(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  const input = (label: string, value: string, set: (v: string) => void, ph: string) => (
    <input aria-label={label} placeholder={ph} value={value} onChange={(e) => set(e.target.value)} />
  );

  return (
    <div className="card" style={{ maxWidth: 560 }}>
      <h2 style={{ fontSize: 16, margin: "4px 0 8px" }}>Get a freight quote — no account needed</h2>
      {error ? <p className="pill red">{error}</p> : null}
      {done ? (
        <>
          <p className="pill green">Request received ✓ reference {done.reference}</p>
          <p>{done.summary}</p>
          {done.missing.length > 0 ? (
            <p className="muted">To quote accurately we may ask about: {done.missing.join(", ")}.</p>
          ) : null}
          <p className="muted">A forwarder will respond shortly. Already a customer? <a href="/login">Sign in</a>.</p>
        </>
      ) : (
        <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {input("Your name / company", name, setName, "Acme Traders")}
          {input("Contact", contact, setContact, "email or phone")}
          {input("Origin", origin, setOrigin, "e.g. Guangzhou")}
          {input("Destination", destination, setDestination, "e.g. Lagos")}
          <textarea aria-label="Shipment details" rows={3} placeholder="e.g. 5 cartons, approx weight, container or air?" value={details} onChange={(e) => setDetails(e.target.value)} />
          <p>
            <button className="btn" type="submit" disabled={busy} style={busy ? { opacity: 0.6 } : undefined}>
              Request quote{busy ? " …" : ""}
            </button>
          </p>
        </form>
      )}
    </div>
  );
}
