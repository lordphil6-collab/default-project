"use client";
import { useCallback, useEffect, useState } from "react";
import { api, Situation } from "../../../lib/api";
import { ActionButton, Card, StatusPill } from "../../../components/primitives";

type RFQ = { id: string; status: string; situation_id: string };
type Quote = { id: string; agent: string; charges: Record<string, number | null>; missing: string[] };
type Compare = {
  rows: { agent: string; total: number | null; missing: string[] }[];
  confidence: string;
  recommendation: { agent: string; reasoning: string } | null;
};
type CustomerQuote = { id: string; status: string; agent_total: number; markup_amount: number; final_price: number };
type FollowUp = { id: string; situation_id: string; bucket: string; status: string; due_at: string | null };
type Exception = { id: string; situation_id: string; category: string; owner: string; next_action: string; status: string };

export default function SituationDetail({ params }: { params: { id: string } }) {
  const sid = params.id;
  const [sit, setSit] = useState<Situation | null>(null);
  const [rfqs, setRfqs] = useState<RFQ[]>([]);
  const [quotes, setQuotes] = useState<Record<string, Quote[]>>({});
  const [compare, setCompare] = useState<Record<string, Compare>>({});
  const [cquotes, setCquotes] = useState<CustomerQuote[]>([]);
  const [fups, setFups] = useState<FollowUp[]>([]);
  const [excs, setExcs] = useState<Exception[]>([]);
  const [error, setError] = useState("");
  const [extractBody, setExtractBody] = useState("");
  const [ingest, setIngest] = useState<Record<string, { agent: string; body: string }>>({});
  const [markup, setMarkup] = useState({ quotation_id: "", kind: "percent", value: "12" });
  const [due, setDue] = useState("");
  const [exc, setExc] = useState({ category: "missing_info", detail: "", owner: "", next: "" });

  const fail = (err: unknown) => setError(err instanceof Error ? err.message : "Failed");

  const refresh = useCallback(async () => {
    setError("");
    try {
      const [s, r, cq, fu, ex] = await Promise.all([
        api<Situation>(`/situations/${sid}`),
        api<RFQ[]>(`/rfqs?situation_id=${sid}`),
        api<CustomerQuote[]>(`/customer-quotes?situation_id=${sid}`),
        api<FollowUp[]>("/follow-ups"),
        api<Exception[]>("/exceptions"),
      ]);
      setSit(s);
      setRfqs(r);
      setCquotes(cq);
      setFups(fu.filter((f) => f.situation_id === sid));
      setExcs(ex.filter((e) => e.situation_id === sid));
      const qmap: Record<string, Quote[]> = {};
      for (const rfq of r) {
        qmap[rfq.id] = await api<Quote[]>(`/rfqs/${rfq.id}/quotations`);
      }
      setQuotes(qmap);
    } catch (err) {
      fail(err);
    }
  }, [sid]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function run(fn: () => Promise<unknown>) {
    setError("");
    try {
      await fn();
      await refresh();
    } catch (err) {
      fail(err);
    }
  }

  return (
    <>
      <Card title={`Situation ${sid.slice(0, 8)}`}>
        {error ? <p className="pill red">{error}</p> : null}
        {!sit ? (
          <p className="muted">Loading…</p>
        ) : (
          <>
            <p>
              <StatusPill tone="amber">{sit.status}</StatusPill>
            </p>
            {sit.missing.length > 0 ? <p className="muted">Missing: {sit.missing.join(", ")}</p> : null}
            {sit.next_action ? <p className="muted">Next: {sit.next_action}</p> : null}
          </>
        )}
      </Card>

      <Card title="Understand — extract & missing">
        <textarea aria-label="Message text" rows={3} style={{ width: "100%" }} placeholder="Paste customer message to extract…" value={extractBody} onChange={(e) => setExtractBody(e.target.value)} />
        <p>
          <ActionButton
            onClick={() => run(() => api(`/situations/${sid}/extract`, { method: "POST", body: JSON.stringify({ body: extractBody }) }))}
          >
            Extract into situation
          </ActionButton>
        </p>
      </Card>

      <Card title={`RFQs (${rfqs.length})`}>
        <p>
          <ActionButton onClick={() => run(() => api("/rfqs", { method: "POST", body: JSON.stringify({ situation_id: sid }) }))}>
            Create RFQ
          </ActionButton>
        </p>
        {rfqs.map((rfq) => (
          <div key={rfq.id} className="card" style={{ marginBottom: 10 }}>
            <p>
              <b className="mono">{rfq.id.slice(0, 8)}</b> <StatusPill tone="indigo">{rfq.status}</StatusPill>{" "}
              <ActionButton secondary onClick={() => run(async () => {
                const cmp = await api<Compare>(`/rfqs/${rfq.id}/compare`);
                setCompare((c) => ({ ...c, [rfq.id]: cmp }));
              })}>
                Compare
              </ActionButton>
            </p>
            {(quotes[rfq.id] || []).map((q) => (
              <p key={q.id} className="muted">
                <b>{q.agent}</b> — freight {q.charges.freight ?? "?"} / origin {q.charges.origin ?? "?"} / dest{" "}
                {q.charges.destination ?? <b>Unknown</b>} {q.missing.length > 0 ? `(missing: ${q.missing.join(", ")})` : ""}
                <span className="mono"> [{q.id.slice(0, 8)}]</span>
              </p>
            ))}
            {compare[rfq.id] ? (
              <p className="muted">
                Confidence: <b>{compare[rfq.id].confidence}</b>
                {compare[rfq.id].recommendation ? ` — ${compare[rfq.id].recommendation!.reasoning}` : " — no comparable quotes yet"}
              </p>
            ) : null}
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>
              <input
                aria-label="Agent name"
                placeholder="Agent name"
                value={ingest[rfq.id]?.agent || ""}
                onChange={(e) => setIngest((m) => ({ ...m, [rfq.id]: { agent: e.target.value, body: m[rfq.id]?.body || "" } }))}
              />
              <input
                aria-label="Quotation text"
                placeholder="Ocean Freight $1,850 … validity 7 days"
                style={{ flex: 1, minWidth: 220 }}
                value={ingest[rfq.id]?.body || ""}
                onChange={(e) => setIngest((m) => ({ ...m, [rfq.id]: { agent: m[rfq.id]?.agent || "", body: e.target.value } }))}
              />
              <ActionButton
                secondary
                onClick={() =>
                  run(() =>
                    api(`/rfqs/${rfq.id}/quotations`, {
                      method: "POST",
                      body: JSON.stringify({ agent: ingest[rfq.id]?.agent || "Agent", body_text: ingest[rfq.id]?.body || "" }),
                    })
                  )
                }
              >
                Ingest quote
              </ActionButton>
            </div>
          </div>
        ))}
      </Card>

      <Card title={`Customer quotes (${cquotes.length})`}>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
          <input aria-label="Agent quotation id" placeholder="agent quote id (8 chars)" style={{ width: 200 }} value={markup.quotation_id} onChange={(e) => setMarkup((m) => ({ ...m, quotation_id: e.target.value }))} />
          <select aria-label="Markup kind" value={markup.kind} onChange={(e) => setMarkup((m) => ({ ...m, kind: e.target.value }))}>
            <option value="percent">percent %</option>
            <option value="fixed">fixed $</option>
            <option value="minimum">minimum %</option>
          </select>
          <input aria-label="Markup value" placeholder="12" style={{ width: 80 }} value={markup.value} onChange={(e) => setMarkup((m) => ({ ...m, value: e.target.value }))} />
          <ActionButton
            secondary
            onClick={() => {
              const qid = Object.values(quotes).flat().find((q) => q.id.startsWith(markup.quotation_id))?.id;
              if (!qid) {
                setError("Pick an agent quotation id shown above (first 8 chars).");
                return;
              }
              run(() =>
                api("/customer-quotes", {
                  method: "POST",
                  body: JSON.stringify({ situation_id: sid, agent_quotation_id: qid, markup_kind: markup.kind, markup_value: Number(markup.value) || 0 }),
                })
              );
            }}
          >
            Price quote
          </ActionButton>
        </div>
        {cquotes.map((q) => (
          <p key={q.id}>
            <b className="mono">${q.final_price.toFixed(2)}</b> (cost {q.agent_total.toFixed(2)} + {q.markup_amount.toFixed(2)}){" "}
            <StatusPill tone={q.status === "Sent" ? "green" : "amber"}>{q.status}</StatusPill>{" "}
            <ActionButton secondary onClick={() => run(() => api(`/customer-quotes/${q.id}/approve`, { method: "POST" }))}>
              Approve (Manager)
            </ActionButton>{" "}
            <ActionButton secondary onClick={() => run(() => api(`/customer-quotes/${q.id}/send`, { method: "POST" }))}>
              Send
            </ActionButton>
          </p>
        ))}
      </Card>

      <Card title={`Follow-ups (${fups.length})`}>
        <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
          <input aria-label="Due date" type="date" value={due} onChange={(e) => setDue(e.target.value)} />
          <ActionButton
            secondary
            onClick={() => run(() => api("/follow-ups", { method: "POST", body: JSON.stringify({ situation_id: sid, due_at: due ? new Date(due).toISOString() : null }) }))}
          >
            Add follow-up
          </ActionButton>
        </div>
        {fups.map((f) => (
          <p key={f.id} className="muted">
            {f.due_at ? f.due_at.slice(0, 10) : "no due"} — {f.bucket} — {f.status}
          </p>
        ))}
        <p>
          {(["Negotiation", "Accepted", "Rejected", "Expired"] as const).map((o) => (
            <span key={o} style={{ marginRight: 8 }}>
              <ActionButton
                secondary
                onClick={() => run(() => api(`/situations/${sid}/outcome`, { method: "POST", body: JSON.stringify({ outcome: o }) }))}
              >
                {o}
              </ActionButton>
            </span>
          ))}
        </p>
      </Card>

      <Card title={`Exceptions (${excs.length})`}>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
          <select aria-label="Category" value={exc.category} onChange={(e) => setExc((x) => ({ ...x, category: e.target.value }))}>
            {["complaint", "delay", "missing_info", "charge", "mismatch", "approval", "conflict", "requirement_change"].map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <input aria-label="Detail" placeholder="What happened" value={exc.detail} onChange={(e) => setExc((x) => ({ ...x, detail: e.target.value }))} />
          <input aria-label="Owner" placeholder="Owner" value={exc.owner} onChange={(e) => setExc((x) => ({ ...x, owner: e.target.value }))} />
          <ActionButton
            secondary
            onClick={() =>
              run(() => api("/exceptions", { method: "POST", body: JSON.stringify({ situation_id: sid, ...exc, next_action: exc.next }) }))
            }
          >
            Log exception
          </ActionButton>
        </div>
        {excs.map((e) => (
          <p key={e.id} className="muted">
            <b>{e.category}</b> — {e.status} — owner {e.owner || "?"} — {e.next_action || "no next action"}{" "}
            {e.status === "Open" ? (
              <ActionButton secondary onClick={() => run(() => api(`/exceptions/${e.id}/resolve`, { method: "POST" }))}>
                Resolve
              </ActionButton>
            ) : null}
          </p>
        ))}
      </Card>
    </>
  );
}
