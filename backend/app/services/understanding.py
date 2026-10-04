"""Phase 3 understanding service — deterministic v1 rules (free, no LLM calls).

Mirrors ai/prompts/v1/*.md. LLM gateway with identical JSON schema lands Phase 5+.
Core rule (PRD Sec 10/13): never invent missing fields.
"""
import re

REQUIRED = ["origin", "destination", "quantity", "weight", "dimensions", "mode", "cargo"]

_LANE = re.compile(r"from\s+([A-Za-z][A-Za-z .'-]{1,60}?)\s+to\s+([A-Za-z][A-Za-z .'-]{1,60}?)(?:[.,]|$)", re.I)
_FALLBACK_LANE = re.compile(r"\b([A-Z][a-z]+)\s+to\s+([A-Z][a-z]+)\b")
_QTY = re.compile(r"(\d+)\s*(cartons?|containers?|pkgs?|packages?|pieces?|boxes?|pallets?|x\s*20ft|x\s*40ft)", re.I)
_EQUIP = re.compile(r"(20\s*ft|40\s*ft|20ft|40ft|20\s*foot|40\s*foot|lcl|fcl)", re.I)
_WEIGHT = re.compile(r"(\d+(?:\.\d+)?)\s*(kg|kgs|tons?|mt)\b", re.I)
_DIMS = re.compile(r"\d+\s*x\s*\d+", re.I)
_MODE = re.compile(r"\b(ocean|sea freight|air freight|air|express|road|rail)\b", re.I)
_INCOTERM = re.compile(r"\b(EXW|FOB|CIF|DAP|DDP|FCA|CPT|CIP)\b", re.I)


def extract_shipment(body: str) -> dict:
    text = body or ""
    out: dict = {
        "origin": None,
        "destination": None,
        "quantity": None,
        "equipment": None,
        "weight_kg": None,
        "dimensions": None,
        "mode": None,
        "incoterm": None,
        "service": None,
        "cargo": None,
        "confidence": {},
    }
    m = _LANE.search(text) or _FALLBACK_LANE.search(text)
    if m:
        out["origin"] = m.group(1).strip()
        out["destination"] = m.group(2).strip(" .")
        out["confidence"]["origin"] = 1.0
        out["confidence"]["destination"] = 1.0
    q = _QTY.search(text)
    if q:
        out["quantity"] = f"{q.group(1)} {q.group(2).lower()}"
        out["confidence"]["quantity"] = 1.0
    e = _EQUIP.search(text)
    if e:
        out["equipment"] = re.sub(r"\s+", "", e.group(1).lower().replace("foot", "ft"))
        out["confidence"]["equipment"] = 1.0
        if not out["quantity"]:
            out["quantity"] = f"1 x {out['equipment']}"
            out["confidence"]["quantity"] = 0.6
    w = _WEIGHT.search(text)
    if w:
        val, unit = float(w.group(1)), w.group(2).lower()
        out["weight_kg"] = val * 1000 if unit.startswith("ton") or unit == "mt" else val
        out["confidence"]["weight"] = 1.0
    if _DIMS.search(text):
        out["dimensions"] = _DIMS.search(text).group(0)  # type: ignore[union-attr]
        out["confidence"]["dimensions"] = 1.0
    md = _MODE.search(text)
    if md:
        raw = md.group(1).lower()
        out["mode"] = "ocean" if "sea" in raw or raw == "ocean" else ("air" if "air" in raw else raw)
        out["confidence"]["mode"] = 1.0
    inc = _INCOTERM.search(text)
    if inc:
        out["incoterm"] = inc.group(1).upper()
        out["confidence"]["incoterm"] = 1.0
    if re.search(r"\bimport\b", text, re.I):
        out["service"] = "import"
    elif re.search(r"\bexport\b", text, re.I):
        out["service"] = "export"
    return out


def detect_missing(ext: dict) -> list[str]:
    missing: list[str] = []
    if not ext.get("origin"):
        missing.append("origin")
    if not ext.get("destination"):
        missing.append("destination")
    if not ext.get("quantity") and not ext.get("equipment"):
        missing.append("quantity")
    if ext.get("weight_kg") is None:
        missing.append("weight")
    if not ext.get("dimensions"):
        missing.append("dimensions")
    if not ext.get("mode"):
        missing.append("mode")
    if not ext.get("cargo"):
        missing.append("cargo")
    return missing


def summarize(ext: dict, missing: list[str]) -> str:
    qty = ext.get("quantity") or ext.get("equipment") or "shipment"
    route = f"from {ext.get('origin')} to {ext.get('destination')}" if ext.get("origin") else "with unclear route"
    svc = f"{ext['service']} " if ext.get("service") else ""
    base = f"{svc}{qty} {route}".strip()
    if ext.get("mode"):
        base += f" by {ext['mode']}"
    if missing:
        base += f". Missing: {', '.join(missing)}."
    return base[0].upper() + base[1:] if base else "Empty enquiry."


def recommend_next_action(missing: list[str]) -> str:
    if missing:
        return f"Request missing info: {', '.join(missing)}"
    return "Create RFQ"
