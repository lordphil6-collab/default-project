import { StatusPill } from "./primitives";

export type Confidence = "High" | "Medium" | "Low";

export function ConfidenceBadge({ level }: { level: Confidence }) {
  const tone = level === "High" ? "green" : level === "Medium" ? "amber" : "red";
  return <StatusPill tone={tone}>{level} confidence</StatusPill>;
}

export function FieldConfidence({
  confirmed,
  assumed,
  missing,
}: {
  confirmed: string[];
  assumed: string[];
  missing: string[];
}) {
  return (
    <div className="conf3">
      <div>
        <b>Confirmed</b>
        <div>{confirmed.join(", ") || "—"}</div>
      </div>
      <div>
        <b>Assumed</b>
        <div>{assumed.join(", ") || "—"}</div>
      </div>
      <div>
        <b>Missing</b>
        <div>{missing.join(", ") || "—"}</div>
      </div>
    </div>
  );
}

export type CompareRow = { param: string; a: string; b: string; c: string; unknownB?: boolean };

export function CompareTable({ rows }: { rows: CompareRow[] }) {
  return (
    <table className="cmp">
      <thead>
        <tr>
          <th>Parameter</th>
          <th>Agent A</th>
          <th>Agent B</th>
          <th>Agent C</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.param}>
            <td>{r.param}</td>
            <td className="mono">{r.a}</td>
            <td className={r.unknownB ? "unk" : "mono"}>{r.b}</td>
            <td className="mono">{r.c}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function SituationCard({
  id,
  route,
  status,
  summary,
  children,
}: {
  id: string;
  route: string;
  status: string;
  summary: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="card">
      <h2 style={{ fontSize: 15, margin: "4px 0" }}>
        {id} — {route} <StatusPill tone="amber">{status}</StatusPill>
      </h2>
      <p className="muted">{summary}</p>
      {children}
    </div>
  );
}

export function ApprovalCard({ total, markup }: { total: string; markup: string }) {
  return (
    <div className="card">
      <h2 style={{ fontSize: 15, margin: "4px 0" }}>Approval — L4 gate</h2>
      <p>
        {total} + {markup} = <b className="mono">$3,270.40</b>
      </p>
      <p className="muted">Human approval required before send. No auto-commit.</p>
    </div>
  );
}
