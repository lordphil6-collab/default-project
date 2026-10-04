"""Eval harness (Phase 8) — runs golden.json through v1 services, reports scores.

Run: python -m backend.app.services.evalharness
Thresholds double as the pilot quality gate (PRD Sec 34).
"""
import json
import pathlib
import sys

from . import quotation as q
from . import understanding as u

GOLDEN = pathlib.Path(__file__).resolve().parents[3] / "ai" / "evals" / "golden.json"


def run_golden(fixtures: dict) -> dict:
    ext_cases = fixtures["extraction"]
    origin_ok = dest_ok = qty_ok = 0
    missing_recall_n = missing_recall_d = 0
    invented = 0
    for case in ext_cases:
        ext = u.extract_shipment(case["body"])
        missing = u.detect_missing(ext)
        if ext.get("origin") == case["origin"]:
            origin_ok += 1
        if ext.get("destination") == case["destination"]:
            dest_ok += 1
        if case.get("quantity") and ext.get("quantity") == case["quantity"]:
            qty_ok += 1
        for m in case.get("must_be_missing", []):
            missing_recall_d += 1
            if m in missing:
                missing_recall_n += 1
        # invention check: stated-missing fields must not be filled (except dims via x-pattern is real)
        if ext.get("weight_kg") is not None and "weight" in case.get("must_be_missing", []):
            invented += 1
    comp = fixtures["comparison"]
    quotes = [
        {"agent": c["agent"],
         "charges": {"freight": c["freight"], "origin": c["origin"], "destination": c["destination"],
                     "other": c.get("other", 0.0)},
         "validity_days": c["validity"], "transit_days": c["transit"]}
        for c in comp["quotes"]
    ]
    res = q.compare_quotes(quotes)
    return {
        "extraction": {
            "origin_acc": origin_ok / len(ext_cases),
            "destination_acc": dest_ok / len(ext_cases),
            "missing_recall": missing_recall_n / max(missing_recall_d, 1),
            "inventions": invented,
        },
        "comparison": {
            "winner": (res["recommendation"] or {}).get("agent"),
            "winner_ok": (res["recommendation"] or {}).get("agent") == comp["expected_winner"],
            "confidence": res["confidence"],
            "confidence_ok": res["confidence"] in comp["expected_confidence"],
            "explained": bool((res["recommendation"] or {}).get("reasoning")),
        },
    }


def gate(scores: dict) -> tuple[bool, list[str]]:
    fails = []
    e, c = scores["extraction"], scores["comparison"]
    if e["origin_acc"] < 1.0:
        fails.append("origin accuracy < 1.0")
    if e["destination_acc"] < 1.0:
        fails.append("destination accuracy < 1.0")
    if e["missing_recall"] < 1.0:
        fails.append("missing recall < 1.0")
    if e["inventions"] > 0:
        fails.append("extractor invented values")
    if not c["winner_ok"]:
        fails.append("wrong recommendation winner")
    if not c["confidence_ok"]:
        fails.append("confidence out of expected band")
    if not c["explained"]:
        fails.append("recommendation unexplained")
    return (not fails, fails)


if __name__ == "__main__":
    fixtures = json.loads(GOLDEN.read_text())
    scores = run_golden(fixtures)
    ok, fails = gate(scores)
    print(json.dumps(scores, indent=2))
    if not ok:
        print("GATE FAIL:", fails)
        sys.exit(1)
    print("GATE PASS")
