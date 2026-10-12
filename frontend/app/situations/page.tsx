"use client";
import { Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api, Situation } from "../../lib/api";
import { ActionButton, Card, StatusPill } from "../../components/primitives";

const PAGE = 25;

function SituationsInner() {
  const params = useSearchParams();
  const q = (params.get("q") || "").toLowerCase();
  const [rows, setRows] = useState<Situation[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState("all");
  const [shown, setShown] = useState(PAGE);

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

  useEffect(() => {
    setShown(PAGE);
  }, [q, status]);

  const filtered = rows.filter((s) => {
    if (status !== "all" && s.status !== status) return false;
    if (!q) return true;
    return [s.id, s.status, s.next_action, ...(s.missing || [])].join(" ").toLowerCase().includes(q);
  });

  return (
    <>
      <Card title={`Situations (${filtered.length})`}>
        {loading ? <p className="muted">Loading…</p> : null}
        {error ? <p className="pill red" role="alert">{error}</p> : null}
        {q ? <p className="muted">Search: “{params.get("q")}” — <a href="/situations">clear</a></p> : null}
        <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
          <select aria-label="Filter by status" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="all">All statuses</option>
            {Array.from(new Set(rows.map((r) => r.status))).map((st) => (
              <option key={st} value={st}>{st}</option>
            ))}
          </select>
        </div>
        {!loading && !error && rows.length === 0 ? (
          <p className="muted">
            None yet — capture one from the <a href="/">dashboard</a>.
          </p>
        ) : null}
        {!loading && !error && rows.length > 0 && filtered.length === 0 ? (
          <p className="muted">No situations match — try clearing the search or filter.</p>
        ) : null}
        {filtered.slice(0, shown).map((s) => (
          <div key={s.id} className="card" style={{ marginBottom: 10 }}>
            <p>
              <b className="mono">{s.id.slice(0, 8)}</b> <StatusPill tone="amber">{s.status}</StatusPill>{" "}
              <a href={`/situations/${s.id}`}>Open →</a>
            </p>
            {s.missing.length > 0 ? <p className="muted">Missing: {s.missing.join(", ")}</p> : null}
            {s.next_action ? <p className="muted">Next: {s.next_action}</p> : null}
          </div>
        ))}
        {filtered.length > shown ? (
          <p>
            <ActionButton secondary onClick={() => setShown((n) => n + PAGE)}>
              Show more ({filtered.length - shown} remaining)
            </ActionButton>
          </p>
        ) : null}
      </Card>
    </>
  );
}

export default function Situations() {
  return (
    <Suspense fallback={<Card title="Situations"><p className="muted">Loading…</p></Card>}>
      <SituationsInner />
    </Suspense>
  );
}
