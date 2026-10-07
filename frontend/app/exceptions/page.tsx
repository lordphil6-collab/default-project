"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";
import { ActionButton, Card, StatusPill } from "../../components/primitives";

type Exception = { id: string; situation_id: string; category: string; owner: string; next_action: string; status: string };

export default function Exceptions() {
  const [rows, setRows] = useState<Exception[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setError("");
    try {
      setRows(await api<Exception[]>("/exceptions"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <Card title={`Exceptions (${rows.length})`}>
      {error ? <p className="pill red">{error}</p> : null}
      {rows.length === 0 && !error ? <p className="muted">No open issues. Log them from the situation detail page.</p> : null}
      {rows.map((e) => (
        <p key={e.id} className="muted">
          <b>{e.category}</b> <StatusPill tone={e.status === "Open" ? "red" : "green"}>{e.status}</StatusPill> — owner {e.owner || "?"}{" "}
          <a href={`/situations/${e.situation_id}`} className="mono">{e.situation_id.slice(0, 8)}</a>{" "}
          {e.status === "Open" ? (
            <ActionButton
              busy={busy === e.id}
              secondary
              onClick={async () => {
                setBusy(e.id);
                setError("");
                try {
                  await api(`/exceptions/${e.id}/resolve`, { method: "POST" });
                  await refresh();
                } catch (err) {
                  setError(err instanceof Error ? err.message : "Failed");
                } finally {
                  setBusy(null);
                }
              }}
            >
              Resolve
            </ActionButton>
          ) : null}
        </p>
      ))}
    </Card>
  );
}
