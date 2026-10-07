"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";
import { Card, StatusPill } from "../../components/primitives";

type FollowUp = { id: string; situation_id: string; bucket: string; status: string; due_at: string | null };

export default function FollowUps() {
  const [rows, setRows] = useState<FollowUp[]>([]);
  const [error, setError] = useState("");

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

  return (
    <Card title={`Follow-ups (${rows.length})`}>
      {error ? <p className="pill red">{error}</p> : null}
      {rows.length === 0 && !error ? <p className="muted">Nothing due — overdue items surface here as urgent.</p> : null}
      {rows.map((f) => (
        <p key={f.id} className="muted">
          <a href={`/situations/${f.situation_id}`} className="mono">{f.situation_id.slice(0, 8)}</a>{" "}
          {f.due_at ? f.due_at.slice(0, 10) : "no due"} <StatusPill tone={f.bucket === "overdue" ? "red" : "amber"}>{f.bucket}</StatusPill>
        </p>
      ))}
    </Card>
  );
}
