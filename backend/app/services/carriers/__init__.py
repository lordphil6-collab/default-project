"""Live carrier adapters — Freightos-style marketplace reach, one plug point.

Each adapter talks to ONE external rate source (carrier API or forwarder
network) and returns normalized rate dicts:

    {"carrier": str, "service": str, "total": float | None, "currency": str,
     "transit_days": int | None, "validity_days": int | None,
     "source": "live", "note": str}

Rules every adapter follows:
- Unconfigured (no creds) -> return [] and name itself in `skipped`.
- Any transport/auth/schema error -> return [] and record the reason in
  `errors`. Live feeds must NEVER crash a quote search.
- Unknown stays Unknown: `total=None` when the feed can't confirm a price.
- No invented prices, no caching of third-party rate data (DHL terms
  forbid storing/revealing rating data without consent).
"""
from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field


@dataclass
class CarrierRequest:
    origin_country: str = ""       # ISO-2, e.g. "CN" (required by most carrier APIs)
    destination_country: str = ""  # ISO-2, e.g. "NG"
    origin_city: str = ""
    destination_city: str = ""
    weight_kg: float | None = None
    pieces: int = 1
    mode: str = ""                 # ocean|air|express


@dataclass
class LiveResult:
    rates: list[dict] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)   # "dhl-express: DHL_API_USER not set"
    errors: list[str] = field(default_factory=list)    # "dhl-express: auth failed"


class CarrierAdapter:
    name = "base"

    def configured(self) -> str | None:
        """None when ready, else the human reason it will be skipped."""
        return "not implemented"

    async def quote(self, req: CarrierRequest) -> list[dict]:
        raise NotImplementedError


_ADAPTERS: list[CarrierAdapter] = []


def register(adapter: CarrierAdapter) -> None:
    _ADAPTERS.append(adapter)


def adapter_names() -> list[str]:
    return [a.name for a in _ADAPTERS]


async def quote_all(req: CarrierRequest, timeout_s: float | None = None) -> LiveResult:
    """Fan out to every registered adapter; one slow/broken feed can't block others."""
    out = LiveResult()
    timeout = timeout_s or float(os.getenv("CARRIER_API_TIMEOUT", "15"))

    async def run(a: CarrierAdapter) -> None:
        reason = a.configured()
        if reason:
            out.skipped.append(f"{a.name}: {reason}")
            return
        try:
            rates = await asyncio.wait_for(a.quote(req), timeout)
            for r in rates or []:
                r["source"] = "live"
                out.rates.append(r)
        except Exception as exc:
            out.errors.append(f"{a.name}: {str(exc)[:200]}")

    await asyncio.gather(*(run(a) for a in _ADAPTERS))
    out.rates.sort(key=lambda r: (r.get("total") is None, r.get("total") or 0))
    return out


# Built-in adapters register themselves on import.
from . import dhl_express as _dhl  # noqa: E402,F401
