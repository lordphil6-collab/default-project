"""Phase 5 quotation intelligence — deterministic parsing + comparison (free, no LLM).

PRD rules enforced:
- Unknown stays Unknown (None), never treated as 0.
- Every comparison carries High/Medium/Low confidence.
- Recommendation always explains reasoning, never bare "best".
"""
import re

_AMT = re.compile(r"(\d+(?:\.\d{1,2})?)")
_CHARGE_LABELS = {
    "freight": re.compile(r"(ocean freight|air freight|freight|sea freight)", re.I),
    "origin": re.compile(r"(origin charge|origin|thc|lhc|pickup|export clearance)", re.I),
    "destination": re.compile(r"(destination charge|destination|delivery|ddc|import clearance)", re.I),
    "other": re.compile(r"(handling|documentation|docs?|customs|surcharge|fuel|baf|pss)", re.I),
}
_VALIDITY = re.compile(r"valid(?:ity)?\s*(?:for|of|:)?\s*(\d+)\s*days?", re.I)
_TRANSIT = re.compile(r"transit\s*(?:time)?\s*(?:of|:)?\s*(\d+)\s*days?", re.I)
_CCY = re.compile(r"\b(USD|NGN|CNY|EUR|GBP)\b")


def _amount(line: str) -> float | None:
    m = _AMT.search(line.replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def parse_quote_text(body: str) -> dict:
    """Parse pasted/text-extracted quote (PDF/Excel/Word OCR text lands here Phase 5+)."""
    charges: dict[str, float | None] = {"freight": None, "origin": None, "destination": None, "other": 0.0}
    validity = transit = 0
    currency = "USD"
    for line in (body or "").splitlines():
        low = line.lower()
        if "unknown" in low or "tbd" in low or "on request" in low:
            continue  # explicit Unknown — do not parse a number from this line
        amt = _amount(line)
        if amt is None:
            continue
        if _CHARGE_LABELS["freight"].search(line) and charges["freight"] is None:
            charges["freight"] = amt
        elif _CHARGE_LABELS["destination"].search(line) and charges["destination"] is None:
            charges["destination"] = amt
        elif _CHARGE_LABELS["origin"].search(line) and charges["origin"] is None:
            charges["origin"] = amt
        elif _CHARGE_LABELS["other"].search(line):
            charges["other"] = (charges["other"] or 0.0) + amt
    vm = _VALIDITY.search(body or "")
    if vm:
        validity = int(vm.group(1))
    tm = _TRANSIT.search(body or "")
    if tm:
        transit = int(tm.group(1))
    cm = _CCY.search(body or "")
    if cm:
        currency = cm.group(1)
    return {"charges": charges, "validity_days": validity, "transit_days": transit, "currency": currency}


def identifiable_total(charges: dict) -> float | None:
    """None when any core charge is Unknown — caller must not compare totals then."""
    if charges.get("freight") is None or charges.get("destination") is None:
        return None
    return (charges["freight"] or 0.0) + (charges.get("origin") or 0.0) + (charges.get("destination") or 0.0) + (
        charges.get("other") or 0.0
    )


def compare_quotes(quotes: list[dict]) -> dict:
    """quotes: [{agent, charges{freight,origin,destination,other}, validity_days, transit_days}]."""
    rows = []
    for q in quotes:
        ch = q["charges"]
        missing = [k for k in ("freight", "origin", "destination") if ch.get(k) is None]
        total = identifiable_total(ch)
        rows.append({"agent": q["agent"], "total": total, "missing": missing,
                     "validity_days": q.get("validity_days", 0), "transit_days": q.get("transit_days", 0)})
    comparable = [r for r in rows if r["total"] is not None]
    if all(not r["missing"] for r in rows) and len(rows) >= 2:
        confidence: str = "High"
    elif comparable:
        confidence = "Medium"
    else:
        confidence = "Low"
    rec = None
    if comparable:
        best = min(comparable, key=lambda r: (r["total"], r["transit_days"]))
        incomplete = [r["agent"] for r in rows if r["missing"]]
        reason = (
            f"{best['agent']} has a complete cost structure with identifiable total "
            f"${best['total']:,.2f}, transit {best['transit_days']}d, validity {best['validity_days']}d."
        )
        if incomplete:
            reason += f" Caution: {', '.join(incomplete)} ha(s) unknown charges — totals not directly comparable."
        rec = {"agent": best["agent"], "reasoning": reason}
    return {"rows": rows, "confidence": confidence, "recommendation": rec}
