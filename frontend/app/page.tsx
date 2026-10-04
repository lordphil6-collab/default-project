import { ActionButton, Card, StatusPill } from "../components/primitives";
import { ApprovalCard, CompareTable, ConfidenceBadge, FieldConfidence, SituationCard } from "../components/domain";

export default function Home() {
  return (
    <>
      <Card title="Today — What needs attention?">
        <p>
          <StatusPill tone="red">3 Urgent</StatusPill> <StatusPill tone="amber">7 Follow-ups</StatusPill>{" "}
          <StatusPill tone="indigo">4 Pending agents</StatusPill> <StatusPill tone="amber">2 Awaiting approval</StatusPill>{" "}
          <StatusPill tone="red">2 Exceptions</StatusPill>
        </p>
        <p className="muted">Prioritised queue, not just info. Phase 1 is static mock data; live data lands Phase 4+.</p>
      </Card>

      <SituationCard
        id="SIT-1042"
        route="20ft China → Lagos"
        status="RFQ In Progress"
        summary="Import freight, 1×20ft. Missing: weight, pickup, incoterm. Next: send RFQ to 3 agents."
      >
        <div style={{ marginBottom: 8 }}>
          <ConfidenceBadge level="Medium" />
        </div>
        <FieldConfidence confirmed={["origin", "destination", "20ft"]} assumed={["ocean freight"]} missing={["weight", "pickup"]} />
        <div className="timeline" style={{ marginTop: 10 }}>
          <div><b>Customer WA:</b> “Need quote for one 20ft China to Lagos”</div>
          <div><b>RFQ sent:</b> Agent A/B/C • B viewed, A opened</div>
        </div>
        <p style={{ marginTop: 10 }}>
          <ActionButton>Approve RFQ send</ActionButton> <ActionButton secondary>Edit clarification</ActionButton>
        </p>
      </SituationCard>

      <Card title="Comparison — Included / Excluded / Unknown">
        <CompareTable
          rows={[
            { param: "Ocean freight", a: "$1,850", b: "$1,720", c: "$1,900" },
            { param: "Destination", a: "$650", b: "Unknown", c: "$580", unknownB: true },
            { param: "Transit", a: "35d", b: "32d", c: "38d" },
            { param: "Total", a: "$2,920", b: "Cannot compare", c: "$2,870?", unknownB: true },
          ]}
        />
        <p className="muted"><b>Recommendation:</b> Agent A — complete costs + competitive total. Unknown ≠ zero.</p>
      </Card>

      <ApprovalCard total="$2,920" markup="12%" />
    </>
  );
}
