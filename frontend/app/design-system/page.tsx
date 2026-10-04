import { ActionButton, Card, StatusPill } from "../../components/primitives";
import { ConfidenceBadge, FieldConfidence } from "../../components/domain";

// Storybook-lite: full Storybook install deferred (heavy). This page is the Phase 1 showcase.
export default function DesignSystem() {
  return (
    <>
      <Card title="Tokens">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5,1fr)", gap: 8 }}>
          {[["#0f172a", "slate-900"], ["#4f46e5", "indigo"], ["#f59e0b", "amber"], ["#16a34a", "green"], ["#dc2626", "red"]].map(
            ([bg, name]) => (
              <div key={name}>
                <div className="swatch" style={{ background: bg }} />
                <div className="muted">{name}</div>
              </div>
            )
          )}
        </div>
        <p className="muted">Type Inter 12/14/16 • tabular-nums • radius 8/12 • 4pt spacing • WCAG AA • keyboard approval flow</p>
      </Card>
      <Card title="Primitives">
        <p>
          <ActionButton>Primary</ActionButton> <ActionButton secondary>Secondary</ActionButton>
        </p>
        <p>
          <StatusPill>Draft</StatusPill> <StatusPill tone="amber">Pending</StatusPill>{" "}
          <StatusPill tone="green">Accepted</StatusPill> <StatusPill tone="red">Expired</StatusPill>{" "}
          <StatusPill tone="indigo">Trial</StatusPill>
        </p>
      </Card>
      <Card title="Domain">
        <p>
          <ConfidenceBadge level="High" /> <ConfidenceBadge level="Medium" /> <ConfidenceBadge level="Low" />
        </p>
        <FieldConfidence confirmed={["origin"]} assumed={["ocean"]} missing={["weight"]} />
      </Card>
    </>
  );
}
