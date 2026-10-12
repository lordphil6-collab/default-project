"""Agent-feedback synthesis + markup recommendation.

Takes every agent quotation on an RFQ (email replies, file uploads, manual
ingest, live feeds) plus the org's updatable pricing rules, and produces ONE
recommended customer price with reasoning a CSR can defend:

- cheapest *identifiable* total wins the base (Unknown totals never win);
- the default pricing rule applies the markup (Standard rule preferred,
  else the first rule); with no rules, an honest ad-hoc fallback is shown
  instead of inventing policy;
- alternatives list every other identifiable quote priced with the same rule;
- lane history flags whether the recommendation beats or trails the typical.

Pure function over rows + rules — trivially testable, no network.
"""
from . import pricing as p


def identifiable_total(charges: dict) -> float | None:
    freight, dest = charges.get("freight"), charges.get("destination")
    if freight is None or dest is None:
        return None
    return round(freight + (charges.get("origin") or 0.0) + dest + (charges.get("other") or 0.0), 2)


def recommend(quotations: list[dict], rules: list[dict], lane_typical: float | None = None) -> dict:
    """quotations: [{id, agent, currency, charges{...}, transit_days}].
    rules: [{id, name, kind, value, min_margin}]."""
    priced = []
    for q in quotations:
        total = identifiable_total(q.get("charges") or {})
        if total is not None:
            priced.append({**q, "agent_total": total})
    unknown = len(quotations) - len(priced)
    if not priced:
        return {"available": False, "reason": "No identifiable agent totals yet — ingest replies or check live rates.",
                "unknown": unknown, "alternatives": []}
    priced.sort(key=lambda r: (r["agent_total"], -(r.get("transit_days") or 0)))
    best = priced[0]
    rule = next((r for r in rules if (r.get("name") or "").lower() == "standard"), None)
    rule = rule or (rules[0] if rules else None)
    if rule:
        kind, value, floor = rule.get("kind", "percent"), rule.get("value", 0.0), rule.get("min_margin", 0.0)
        calc = p.apply_markup(best["agent_total"], kind, value, floor)
        applied = {"id": rule.get("id"), "name": rule.get("name"), "kind": rule.get("kind"),
                   "value": rule.get("value")}
        reasoning = (f"{best['agent']} is cheapest identifiable at "
                     f"{best.get('currency', 'USD')} {best['agent_total']:,.2f}; "
                     f"rule “{rule.get('name')}” ({rule.get('kind')} {rule.get('value')}) applies.")
    else:
        kind, value, floor = "percent", 12.0, 0.0
        calc = p.apply_markup(best["agent_total"], kind, value, floor)
        applied = None
        reasoning = (f"{best['agent']} is cheapest identifiable at "
                     f"{best.get('currency', 'USD')} {best['agent_total']:,.2f}; "
                     f"no saved pricing rule — 12% ad-hoc fallback shown, save a rule in /pricing.")
    verdict = None
    if lane_typical:
        verdict = ("beats lane typical" if calc["final_price"] <= lane_typical
                   else "trails lane typical — review margin")
    alternatives = []
    for alt in priced[1:]:
        c = p.apply_markup(alt["agent_total"], kind, value, floor)
        alternatives.append({"agent": alt["agent"], "agent_total": alt["agent_total"],
                             "final_price": c["final_price"]})
    return {"available": True, "agent_quotation_id": best.get("id"), "agent": best["agent"],
            "agent_total": best["agent_total"], "currency": best.get("currency", "USD"),
            "rule": applied, "markup_amount": calc["markup_amount"], "final_price": calc["final_price"],
            "reasoning": reasoning, "lane_verdict": verdict, "unknown": unknown,
            "alternatives": alternatives}
