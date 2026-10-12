"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "../../../lib/api";
import { ActionButton, Card } from "../../../components/primitives";

type Box = { id: string; provider: string; host: string; port: number; username: string; last_uid: number; status: string };

const PRESETS: Record<string, { host: string; port: string; hint: string }> = {
  gmail: { host: "imap.gmail.com", port: "993", hint: "Google Account → 2-Step → App passwords (16 chars)." },
  outlook: { host: "outlook.office365.com", port: "993", hint: "account.microsoft.com → Security → App passwords." },
  webmail: { host: "", port: "993", hint: "Your host's IMAP server (cPanel/Plesk webmail usually imap.yourdomain.com :993 SSL)." },
};

export default function MailboxSettings() {
  const [rows, setRows] = useState<Box[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [provider, setProvider] = useState("gmail");
  const [form, setForm] = useState({ host: PRESETS.gmail.host, port: PRESETS.gmail.port, username: "", password: "" });

  function pickProvider(p: string) {
    setProvider(p);
    setForm((f) => ({ ...f, host: PRESETS[p].host, port: PRESETS[p].port }));
  }

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
      await api("/mailboxes", {
        method: "POST",
        body: JSON.stringify({
          provider,
          host: form.host.trim(),
          port: Number(form.port) || 993,
          username: form.username.trim(),
          password: form.password,
        }),
      });
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
        {error ? <p className="pill red" role="alert">{error}</p> : null}
        {notice ? <p className="pill green" role="status">{notice}</p> : null}
        <div style={{ display: "flex", gap: 8, marginBottom: 8 }} role="group" aria-label="Provider">
          {(["gmail", "outlook", "webmail"] as const).map((p) => (
            <button
              key={p}
              type="button"
              className={provider === p ? "btn" : "btn sec"}
              style={{ padding: "4px 12px", fontSize: 13 }}
              onClick={() => pickProvider(p)}
            >
              {p === "gmail" ? "Gmail" : p === "outlook" ? "Outlook" : "Webmail / other"}
            </button>
          ))}
        </div>
        <form onSubmit={connect} style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <input aria-label="IMAP host" value={form.host} onChange={(e) => setForm((f) => ({ ...f, host: e.target.value }))} placeholder={provider === "webmail" ? "imap.yourdomain.com" : "IMAP host"} />
          <input aria-label="IMAP port" style={{ width: 80 }} value={form.port} onChange={(e) => setForm((f) => ({ ...f, port: e.target.value }))} />
          <input aria-label="Username" placeholder="you@gmail.com" value={form.username} onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))} />
          <input aria-label="App password" type="password" placeholder="app password" value={form.password} onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} />
          <ActionButton busy={busy === "connect"} submit>Connect</ActionButton>
        </form>
        <p className="muted">{PRESETS[provider].hint} Replies auto-ingest on the next poll (30-min worker or “Poll now”).</p>
      </Card>
      <Card title={`Mailboxes (${rows.length})`}>
        {rows.map((b) => (
          <p key={b.id} className="muted">
            <b>{b.username}</b> @ {b.host}:{b.port} ({b.provider}) — last UID {b.last_uid} — {b.status}{" "}
            <ActionButton busy={busy === b.id} secondary onClick={() => poll(b.id)}>
              Poll now
            </ActionButton>
          </p>
        ))}
      </Card>
    </>
  );
}
