"use client";
import { useCallback, useEffect, useState } from "react";
import { api, Situation } from "../../lib/api";
import { Card, StatusPill } from "../../components/primitives";

export default function Situations() {
  const [rows, setRows] = useState<Situation[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setRows(await api<Situation[]>("/situations"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <>
      <Card title={`Situations (${rows.length})`}>
        {loading ? <p className="muted">Loading…</p> : null}
        {error ? <p className="pill red">{error}</p> : null}
        {!loading && !error && rows.length === 0 ? (
          <p className="muted">
            None yet — capture one from the <a href="/">dashboard</a>.
          </p>
        ) : null}
        {rows.map((s) => (
          <div key={s.id} className="card" style={{ marginBottom: 10 }}>
            <p>
              <b className="mono">{s.id.slice(0, 8)}</b> <StatusPill tone="amber">{s.status}</StatusPill>{" "}
              <a href={`/situations/${s.id}`}>Open →</a>
            </p>
            {s.missing.length > 0 ? <p className="muted">Missing: {s.missing.join(", ")}</p> : null}
            {s.next_action ? <p className="muted">Next: {s.next_action}</p> : null}
          </div>
        ))}
      </Card>
    </>
  );
}
