"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";
import { ActionButton, Card, StatusPill } from "../../components/primitives";

type FollowUp = { id: string; situation_id: string; bucket: string; status: string; due_at: string | null };

export default function FollowUps() {
  const [rows, setRows] = useState<FollowUp[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setRows(await api<FollowUp[]>("/follow-ups"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function done(id: string) {
    setBusy(id);
    setError("");
    try {
      await api(`/follow-ups/${id}/done`, { method: "POST" });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <Card title={`Follow-ups (${rows.length})`}>
      {error ? <p className="pill red" role="alert">{error}</p> : null}
      {rows.length === 0 && !error ? <p className="muted">Nothing due — overdue items surface here as urgent.</p> : null}
      {rows.map((f) => (
        <p key={f.id} className="muted">
          <a href={`/situations/${f.situation_id}`} className="mono">{f.situation_id.slice(0, 8)}</a>{" "}
          {f.due_at ? f.due_at.slice(0, 10) : "no due"} <StatusPill tone={f.bucket === "overdue" ? "red" : "amber"}>{f.bucket}</StatusPill>{" "}
          <StatusPill tone={f.status === "Done" ? "green" : "default"}>{f.status}</StatusPill>{" "}
          {f.status !== "Done" ? (
            <ActionButton busy={busy === f.id} secondary onClick={() => done(f.id)}>
              Mark done
            </ActionButton>
          ) : null}
        </p>
      ))}
    </Card>
  );
}
