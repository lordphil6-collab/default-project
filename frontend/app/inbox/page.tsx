"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";
import { Card, StatusPill } from "../../components/primitives";

type Thread = {
  conversation_id: string;
  situation_id: string;
  status: string;
  channel: string;
  preview: string;
};

type Msg = { id: string; channel: string; body: string };

export default function Inbox() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [open, setOpen] = useState<string | null>(null);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      setThreads(await api<Thread[]>("/inbox"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function show(cid: string) {
    setError("");
    try {
      setOpen(cid);
      setMsgs(await api<Msg[]>(`/conversations/${cid}/messages`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    }
  }

  return (
    <>
      <Card title={`Inbox (${threads.length})`}>
        {error ? <p className="pill red">{error}</p> : null}
        {threads.length === 0 && !error ? <p className="muted">No conversations yet — capture an enquiry first.</p> : null}
        {threads.map((t) => (
          <p key={t.conversation_id}>
            <StatusPill tone="indigo">{t.channel}</StatusPill> <StatusPill tone="amber">{t.status}</StatusPill>{" "}
            <a href={`/situations/${t.situation_id}`} className="mono">{t.situation_id.slice(0, 8)}</a> — {t.preview}{" "}
            <button className="btn sec" type="button" onClick={() => show(t.conversation_id)}>
              Read
            </button>
          </p>
        ))}
      </Card>
      {open ? (
        <Card title="Thread">
          {msgs.map((m) => (
            <p key={m.id} className="muted">
              <b>[{m.channel}]</b> {m.body}
            </p>
          ))}
        </Card>
      ) : null}
    </>
  );
}
