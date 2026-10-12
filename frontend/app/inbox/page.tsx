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
  const [notice, setNotice] = useState("");
  const [reply, setReply] = useState("");
  const [sending, setSending] = useState(false);
  const [channel, setChannel] = useState("all");
  const [brief, setBrief] = useState<null | {
    situation_id: string; messages: number; channels: string[]; combined: string;
    extraction: Record<string, unknown>; missing: string[]; summary: string;
    next_action: string; default_channel: string;
  }>(null);
  const [briefBusy, setBriefBusy] = useState(false);

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
    setReply("");
    setBrief(null);
    try {
      setOpen(cid);
      setMsgs(await api<Msg[]>(`/conversations/${cid}/messages`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    }
  }

  async function prepare() {
    if (!open) return;
    setBriefBusy(true);
    setError("");
    try {
      setBrief(await api(`/conversations/${open}/brief`, { method: "POST" }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBriefBusy(false);
    }
  }

  async function createFromBrief() {
    if (!open || !brief) return;
    setSending(true);
    setError("");
    try {
      const ch = brief.default_channel === "email" || brief.default_channel === "whatsapp" ? brief.default_channel : "web";
      const sit = await api<{ id: string }>("/intake", {
        method: "POST",
        body: JSON.stringify({
          customer_name: `Inbox thread ${open.slice(0, 8)}`,
          channel: ch,
          body: brief.combined.slice(0, 2000),
        }),
      });
      window.location.href = `/situations/${sit.id}`;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setSending(false);
    }
  }

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!open || !reply.trim()) return;
    setSending(true);
    setError("");
    setNotice("");
    try {
      await api(`/conversations/${open}/messages`, {
        method: "POST",
        body: JSON.stringify({ body: reply.trim(), channel: "web" }),
      });
      setReply("");
      setMsgs(await api<Msg[]>(`/conversations/${open}/messages`));
      setNotice("Reply recorded ✓");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setSending(false);
    }
  }

  const visible = channel === "all" ? threads : threads.filter((t) => t.channel === channel);

  return (
    <>
      <Card title={`Inbox (${visible.length})`}>
        {error ? <p className="pill red" role="alert">{error}</p> : null}
        {notice ? <p className="pill green" role="status">{notice}</p> : null}
        <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
          <select aria-label="Filter by channel" value={channel} onChange={(e) => setChannel(e.target.value)}>
            <option value="all">All channels</option>
            {Array.from(new Set(threads.map((t) => t.channel))).map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
        {visible.length === 0 && !error ? <p className="muted">No conversations yet — capture an enquiry first.</p> : null}
        {visible.map((t) => (
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
          <form onSubmit={send} style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <input
              aria-label="Reply"
              placeholder="Write a reply…"
              style={{ flex: 1 }}
              value={reply}
              onChange={(e) => setReply(e.target.value)}
            />
            <button className="btn" type="submit" disabled={sending || !reply.trim()}>
              Reply{sending ? " …" : ""}
            </button>
            <button className="btn sec" type="button" disabled={briefBusy} onClick={prepare}>
              Prepare RFQ brief{briefBusy ? " …" : ""}
            </button>
          </form>
          {brief ? (
            <div className="card" style={{ marginTop: 8 }}>
              <p><b>RFQ brief</b> — {brief.messages} message(s), {brief.missing.length} missing</p>
              <p className="muted">{brief.summary}</p>
              {brief.missing.length > 0 ? <p className="muted">Missing: {brief.missing.join(", ")}</p> : null}
              <p className="muted">Next: {brief.next_action}</p>
              <p>
                <button className="btn" type="button" disabled={sending} onClick={createFromBrief}>
                  Create situation from brief
                </button>{" "}
                <a href={`/situations/${brief.situation_id}`}>Open linked situation →</a>
              </p>
            </div>
          ) : null}
        </Card>
      ) : null}
    </>
  );
}
