"""DHL Express adapter — live account rates via the MyDHL Rating API.

Setup (https://developer.dhl.com → Register → DHL Express → Get Access):
  1. You need an ACTIVE DHL Express customer account (rates are account-based).
  2. Your DHL consultant provisions API credentials (HTTP Basic Auth user/password).
  3. Set the env vars below and restart the API. Test env allows 500 calls/day.

Env:
  DHL_API_USER / DHL_API_PASSWORD  Basic Auth credentials from DHL
  DHL_ACCOUNT_NUMBER               your 9-digit Express account number
  DHL_API_BASE                     default test env; set to the prod URL for live money

What it returns: one row per DHL product (Express Worldwide, Economy Select,
...) with account total + currency + delivery estimate. Indicative only —
final rate/transit can differ at tender (DHL terms). Requires ISO-2 country
codes; city names alone are not enough for the Rating API.
"""
from __future__ import annotations

import os
from datetime import date, timedelta

import httpx

from . import CarrierAdapter, CarrierRequest, register


class DHLExpressAdapter(CarrierAdapter):
    name = "dhl-express"

    def configured(self) -> str | None:
        missing = [k for k in ("DHL_API_USER", "DHL_API_PASSWORD", "DHL_ACCOUNT_NUMBER")
                   if not os.getenv(k)]
        if missing:
            return f"{', '.join(missing)} not set — see docs/CARRIERS.md"
        return None

    def _base(self) -> str:
        return os.getenv("DHL_API_BASE", "https://express.api.dhl.com/mydhlapi/test").rstrip("/")

    def _params(self, req: CarrierRequest) -> dict:
        if not req.origin_country or not req.destination_country:
            raise ValueError("origin_country + destination_country (ISO-2) required")
        return {
            "accountNumber": os.getenv("DHL_ACCOUNT_NUMBER", ""),
            "originCountryCode": req.origin_country.upper(),
            "originCityName": req.origin_city or "Unknown",
            "destinationCountryCode": req.destination_country.upper(),
            "destinationCityName": req.destination_city or "Unknown",
            "weight": req.weight_kg or 1.0,
            "length": 1, "width": 1, "height": 1,
            "plannedShippingDate": (date.today() + timedelta(days=1)).isoformat(),
            "isCustomsDeclarable": "true",
            "unitOfMeasurement": "metric",
        }

    @staticmethod
    def _parse(payload: dict) -> list[dict]:
        """Defensive walk of the Rating response — schema drift must not crash us."""
        out = []
        products = payload.get("products") or []
        for p in products:
            if not isinstance(p, dict):
                continue
            prices = p.get("totalPrice") or p.get("prices") or []
            if isinstance(prices, dict):
                prices = [prices]
            total, currency = None, (p.get("currency") or "USD")
            for pr in prices:
                if not isinstance(pr, dict):
                    continue
                for key in ("price", "totalNet", "total", "value"):
                    v = pr.get(key)
                    if isinstance(v, (int, float)):
                        total = float(v)
                        currency = pr.get("priceCurrency") or pr.get("currency") or currency
                        break
                if total is not None:
                    break
            delivery = p.get("deliveryCapabilities") or {}
            out.append({
                "carrier": "DHL Express",
                "service": str(p.get("productName") or p.get("productCode") or "Express"),
                "total": total,
                "currency": str(currency),
                "transit_days": delivery.get("totalTransitDays"),
                "validity_days": 7,
                "note": "indicative account rate",
            })
        return out

    async def quote(self, req: CarrierRequest) -> list[dict]:
        params = self._params(req)
        auth = (os.getenv("DHL_API_USER", ""), os.getenv("DHL_API_PASSWORD", ""))
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(f"{self._base()}/rates", params=params, auth=auth)
            if resp.status_code == 401:
                raise RuntimeError("DHL auth failed — check DHL_API_USER/PASSWORD + account")
            resp.raise_for_status()
            return self._parse(resp.json())


register(DHLExpressAdapter())
