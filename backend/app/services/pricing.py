"""Phase 6 pricing service — company-defined rules only. AI never sets policy.

Kinds: percent | fixed | minimum | combined (percent + fixed).
min_margin floors the markup_amount. All money rounded to 2dp.
"""


def apply_markup(agent_total: float, kind: str, value: float, min_margin: float = 0.0) -> dict:
    if agent_total < 0:
        raise ValueError("agent_total must be >= 0")
    kind = (kind or "percent").lower()
    if kind == "percent":
        markup = agent_total * (value / 100.0)
    elif kind == "fixed":
        markup = value
    elif kind == "minimum":
        markup = max(agent_total * (value / 100.0), min_margin)
    elif kind == "combined":
        # value = percent; min_margin reused as fixed add-on for combined rules
        markup = agent_total * (value / 100.0) + min_margin
    else:
        raise ValueError(f"unknown markup kind: {kind}")
    markup = max(round(markup, 2), round(min_margin if kind != "combined" else 0.0, 2))
    final = round(agent_total + markup, 2)
    return {"agent_total": round(agent_total, 2), "markup_amount": markup, "final_price": final}
