"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "../../../lib/api";
import { ActionButton, Card } from "../../../components/primitives";

type Box = { id: string; provider: string; host: string; username: string; last_uid: number; status: string };

export default function MailboxSettings() {
  const [rows, setRows] = useState<Box[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [form, setForm] = useState({ host: "imap.gmail.com", username: "", password: "" });

  const refresh = useCallback(async () => {
    setError("");
    try {
      setRows(await api<Box[]>("/mailboxes"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed (Manager+ only)");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function connect(e: React.FormEvent) {
    e.preventDefault();
    setBusy("connect");
    setError("");
    setNotice("");
    try {
      await api("/mailboxes", { method: "POST", body: JSON.stringify({ ...form, provider: "imap" }) });
      setNotice("Mailbox connected ✓ password stored encrypted");
      setForm((f) => ({ ...f, password: "" }));
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(null);
    }
  }

  async function poll(id: string) {
    setBusy(id);
    setError("");
    setNotice("");
    try {
      const r = await api<{ fetched: number; auto_quotations: number; situations: number }>(
        `/mailboxes/${id}/poll`, { method: "POST" });
      setNotice(`Polled ✓ ${r.fetched} new, ${r.auto_quotations} auto-quotations, ${r.situations} new situations`);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <Card title="Connect mailbox (Manager+)">
        {error ? <p className="pill red">{error}</p> : null}
        {notice ? <p className="pill green">{notice}</p> : null}
        <form onSubmit={connect} style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <input aria-label="IMAP host" value={form.host} onChange={(e) => setForm((f) => ({ ...f, host: e.target.value }))} />
          <input aria-label="Username" placeholder="you@gmail.com" value={form.username} onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))} />
          <input aria-label="App password" type="password" placeholder="app password" value={form.password} onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} />
          <ActionButton busy={busy === "connect"} submit>Connect</ActionButton>
        </form>
        <p className="muted">Gmail: Google Account → Security → 2-Step → App passwords. Outlook: account.microsoft.com → Security → App passwords.</p>
      </Card>
      <Card title={`Mailboxes (${rows.length})`}>
        {rows.map((b) => (
          <p key={b.id} className="muted">
            <b>{b.username}</b> @ {b.host} — last UID {b.last_uid} — {b.status}{" "}
            <ActionButton busy={busy === b.id} secondary onClick={() => poll(b.id)}>
              Poll now
            </ActionButton>
          </p>
        ))}
      </Card>
    </>
  );
}
