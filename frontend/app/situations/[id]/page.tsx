"use client";
import { useCallback, useEffect, useState } from "react";
import { api, apiForm, Situation } from "../../../lib/api";
import { ActionButton, Card, StatusPill } from "../../../components/primitives";

type RFQ = { id: string; status: string; situation_id: string };
type Quote = { id: string; agent: string; charges: Record<string, number | null>; missing: string[] };
type Compare = {
  rows: { agent: string; total: number | null; missing: string[]; rank: number | null; badges: string[]; validity_days: number; transit_days: number }[];
  confidence: string;
  recommendation: { agent: string; reasoning: string } | null;
};
type Guideline = {
  available: boolean; basis: string; confidence: string; low?: number; typical?: number; high?: number;
  count?: number; fastest_transit_days?: number | null; note?: string;
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
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [extractBody, setExtractBody] = useState("");
  const [ingest, setIngest] = useState<Record<string, { agent: string; body: string }>>({});
  const [markup, setMarkup] = useState({ quotation_id: "", kind: "percent", value: "12" });
  const [due, setDue] = useState("");
  const [sendTo, setSendTo] = useState("");
  const [sendChannel, setSendChannel] = useState("logged");
  const [matched, setMatched] = useState<{ agent_id: string; agent: string; score: number; reasons: string[] }[]>([]);
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [guide, setGuide] = useState<Guideline | null>(null);
  const [exc, setExc] = useState({ category: "missing_info", detail: "", owner: "", next: "" });

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
      setError(err instanceof Error ? err.message : "Load failed");
    }
  }, [sid]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function act(key: string, label: string, fn: () => Promise<unknown>) {
    setBusy(key);
    setError("");
    try {
      await fn();
      setNotice(`${label} ✓`);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <Card title={`Situation ${sid.slice(0, 8)}`}>
        {error ? <p className="pill red">{error}</p> : null}
        {notice ? <p className="pill green">{notice}</p> : null}
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
            busy={busy === "extract"}
            onClick={() => act("extract", "Extracted into situation", () => api(`/situations/${sid}/extract`, { method: "POST", body: JSON.stringify({ body: extractBody }) }))}
          >
            Extract into situation
          </ActionButton>
        </p>
      </Card>

      <Card title="Instant estimate — from past quotes">
        {!guide ? (
          <p>
            <ActionButton
              busy={busy === "guide"}
              secondary
              onClick={() => act("guide", "Guideline estimated from history", async () => {
                setGuide(await api<Guideline>(`/situations/${sid}/guideline`));
              })}
            >
              Estimate now
            </ActionButton>{" "}
            <span className="muted">No waiting for agents — based on comparable history.</span>
          </p>
        ) : guide.available ? (
          <p>
            <b className="mono">${guide.low?.toLocaleString()} – ${guide.high?.toLocaleString()}</b>{" "}
            (typical <b className="mono">${guide.typical?.toLocaleString()}</b>){" "}
            <StatusPill tone={guide.confidence === "High" ? "green" : "amber"}>{guide.confidence}</StatusPill>
            <span className="muted">
              {" "}· {guide.basis} · {guide.count} quote(s)
              {guide.fastest_transit_days ? ` · fastest seen ${guide.fastest_transit_days}d` : ""}
            </span>
          </p>
        ) : (
          <p className="muted">{guide.note}</p>
        )}
      </Card>

      <Card title={`RFQs (${rfqs.length})`}>
        <p>
          <ActionButton busy={busy === "rfq"} onClick={() => act("rfq", "RFQ created", () => api("/rfqs", { method: "POST", body: JSON.stringify({ situation_id: sid }) }))}>
            Create RFQ
          </ActionButton>
        </p>
        <p>
          <ActionButton busy={busy === "match"} secondary onClick={() => act("match", "Agents ranked by lane, service and capability", async () => {
            setMatched(await api<{ agent_id: string; agent: string; score: number; reasons: string[] }[]>(`/agents/match?situation_id=${sid}`));
          })}>
            Recommend agents
          </ActionButton>
        </p>
        {matched.map((m) => (
          <p key={m.agent_id} className="muted">
            <input
              type="checkbox"
              aria-label={`Select ${m.agent}`}
              checked={!!selected[m.agent_id]}
              onChange={(e) => setSelected((s) => ({ ...s, [m.agent_id]: e.target.checked }))}
            />{" "}
            <b>{m.agent}</b> — score {m.score}: {m.reasons.join("; ")}
          </p>
        ))}
        {rfqs.map((rfq) => (
          <div key={rfq.id} className="card" style={{ marginBottom: 10 }}>
            <p>
              <b className="mono">{rfq.id.slice(0, 8)}</b> <StatusPill tone="indigo">{rfq.status}</StatusPill>{" "}
              <ActionButton
                busy={busy === `dist-${rfq.id}`}
                secondary
                onClick={() => {
                  const ids = Object.keys(selected).filter((k) => selected[k]);
                  if (ids.length === 0) {
                    setError("Tick at least one recommended agent first.");
                    return;
                  }
                  act(`dist-${rfq.id}`, `RFQ sent to ${ids.length} agent(s)`, async () => {
                    await api(`/rfqs/${rfq.id}/recipients`, { method: "POST", body: JSON.stringify({ agent_ids: ids }) });
                    await api(`/rfqs/${rfq.id}/send`, { method: "POST" });
                  });
                }}
              >
                Send to selected
              </ActionButton>{" "}
              <ActionButton busy={busy === `cmp-${rfq.id}`} secondary onClick={() => act(`cmp-${rfq.id}`, "Comparison refreshed", async () => {
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
              <>
                <p className="muted">
                  Confidence: <b>{compare[rfq.id].confidence}</b>
                  {compare[rfq.id].recommendation ? ` — ${compare[rfq.id].recommendation!.reasoning}` : " — no comparable quotes yet"}
                </p>
                <table className="cmp">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Agent</th>
                      <th>All-in total</th>
                      <th>Transit</th>
                      <th>Validity</th>
                      <th>Flags</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...compare[rfq.id].rows]
                      .sort((a, b) => (a.rank ?? 999) - (b.rank ?? 999))
                      .map((r) => (
                        <tr key={r.agent}>
                          <td>{r.rank ?? "—"}</td>
                          <td>{r.agent}</td>
                          <td className="mono">{r.total != null ? `$${r.total.toLocaleString()}` : "cannot compare"}</td>
                          <td>{r.transit_days ? `${r.transit_days}d` : "?"}</td>
                          <td>{r.validity_days ? `${r.validity_days}d` : "?"}</td>
                          <td>
                            {r.badges.map((b) => (
                              <span key={b}>
                                <StatusPill tone={b === "cheapest" ? "green" : b === "fastest" ? "indigo" : "amber"}>{b}</StatusPill>{" "}
                              </span>
                            ))}
                            {r.missing.length > 0 ? <span className="muted">missing {r.missing.join(", ")}</span> : null}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </>
            ) : null}
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>
              <input
                aria-label="Quotation file"
                type="file"
                accept=".pdf,.xlsx,.xlsm,.docx,.txt,.csv"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (!f) return;
                  const form = new FormData();
                  form.append("agent", ingest[rfq.id]?.agent || "Agent");
                  form.append("file", f);
                  act(`up-${rfq.id}`, `File ${f.name} ingested`, () => apiForm(`/rfqs/${rfq.id}/quotations/upload`, form));
                }}
              />
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
                busy={busy === `ing-${rfq.id}`}
                secondary
                onClick={() =>
                  act(`ing-${rfq.id}`, "Quotation ingested", () =>
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
            busy={busy === "price"}
            secondary
            onClick={() => {
              const qid = Object.values(quotes).flat().find((q) => q.id.startsWith(markup.quotation_id))?.id;
              if (!qid) {
                setError("Pick an agent quotation id shown above (first 8 chars).");
                return;
              }
              act("price", "Customer quote priced", () =>
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
            <ActionButton busy={busy === `ap-${q.id}`} secondary onClick={() => act(`ap-${q.id}`, "Quote approved — needs Manager role", () => api(`/customer-quotes/${q.id}/approve`, { method: "POST" }))}>
              Approve (Manager)
            </ActionButton>{" "}
            <ActionButton busy={busy === `se-${q.id}`} secondary onClick={() => act(`se-${q.id}`, `Quote sent via ${sendChannel}`, () => api(`/customer-quotes/${q.id}/send`, { method: "POST", body: JSON.stringify({ channel: sendChannel, to: sendTo }) }))}>
              Send
            </ActionButton>
          </p>
        ))}
        <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
          <select aria-label="Delivery channel" value={sendChannel} onChange={(e) => setSendChannel(e.target.value)}>
            <option value="logged">record only</option>
            <option value="email">email (SMTP)</option>
            <option value="whatsapp">WhatsApp</option>
          </select>
          <input aria-label="Send to" placeholder="email or phone (for email/WhatsApp)" style={{ minWidth: 220 }} value={sendTo} onChange={(e) => setSendTo(e.target.value)} />
        </div>
      </Card>

      <Card title={`Follow-ups (${fups.length})`}>
        <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
          <input aria-label="Due date" type="date" value={due} onChange={(e) => setDue(e.target.value)} />
          <ActionButton
            busy={busy === "fup"}
            secondary
            onClick={() => act("fup", "Follow-up added", () => api("/follow-ups", { method: "POST", body: JSON.stringify({ situation_id: sid, due_at: due ? new Date(due).toISOString() : null }) }))}
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
                busy={busy === `oc-${o}`}
                secondary
                onClick={() => act(`oc-${o}`, `Outcome recorded: ${o}`, () => api(`/situations/${sid}/outcome`, { method: "POST", body: JSON.stringify({ outcome: o }) }))}
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
            busy={busy === "exc"}
            secondary
            onClick={() =>
              act("exc", "Exception logged", () => api("/exceptions", { method: "POST", body: JSON.stringify({ situation_id: sid, ...exc, next_action: exc.next }) }))
            }
          >
            Log exception
          </ActionButton>
        </div>
        {excs.map((e) => (
          <p key={e.id} className="muted">
            <b>{e.category}</b> — {e.status} — owner {e.owner || "?"} — {e.next_action || "no next action"}{" "}
            {e.status === "Open" ? (
              <ActionButton busy={busy === `re-${e.id}`} secondary onClick={() => act(`re-${e.id}`, "Exception resolved", () => api(`/exceptions/${e.id}/resolve`, { method: "POST" }))}>
                Resolve
              </ActionButton>
            ) : null}
          </p>
        ))}
      </Card>
    </>
  );
}
