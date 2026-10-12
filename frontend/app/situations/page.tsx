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
      <Card title={`Pipeline — synthesized requests (${filtered.length})`}>
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
            Empty pipeline — capture an enquiry from the <a href="/">dashboard</a>, connect a{" "}
            <a href="/settings/mailbox">mailbox</a>, or synthesize an <a href="/inbox">inbox thread</a>.
          </p>
        ) : null}
        {!loading && !error && rows.length > 0 && filtered.length === 0 ? (
          <p className="muted">No requests match — try clearing the search or filter.</p>
        ) : null}
        {filtered.length > 0 ? (
          <table className="cmp">
            <caption className="sr-only">Synthesized requests ready for quoting</caption>
            <thead>
              <tr>
                <th>Ref</th>
                <th>Route</th>
                <th>Mode</th>
                <th>Status</th>
                <th>Missing</th>
                <th>Next</th>
                <th>Quote</th>
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, shown).map((s) => (
                <tr key={s.id}>
                  <td className="mono">{s.id.slice(0, 8)}</td>
                  <td>{routeOf(s)}</td>
                  <td>{s.mode || "—"}</td>
                  <td><StatusPill tone="amber">{s.status}</StatusPill></td>
                  <td>{s.missing.length > 0 ? s.missing.join(", ") : <span className="pill green">ready</span>}</td>
                  <td className="muted">{s.next_action || "—"}</td>
                  <td><a href={`/situations/${s.id}`}>Open →</a></td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
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
    <Suspense fallback={<Card title="Pipeline"><p className="muted">Loading…</p></Card>}>
      <SituationsInner />
    </Suspense>
  );
}

function routeOf(s: Situation): string {
  const o = (s.origin || "").trim();
  const d = (s.destination || "").trim();
  if (o || d) return `${o || "?"} → ${d || "?"}`;
  return "—";
}
