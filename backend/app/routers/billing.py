"""SaaS billing checkout + provider webhooks (Stripe + Paystack).

Without provider secrets configured the endpoints answer 501 with setup
guidance instead of failing obscurely. Webhook signature checks are real and
unit-tested; they activate with the same secrets.
"""
import hashlib
import hmac
import os

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import CurrentUser, get_current_user, require_roles
from ..models import Entitlement, Organization, Plan
from ..services.audit import log_action
from .intake import _session

router = APIRouter()


class CheckoutIn(BaseModel):
    plan_id: str
    success_url: str = ""
    cancel_url: str = ""


def _stripe_key() -> str:
    return os.getenv("STRIPE_SECRET_KEY", "")


def _paystack_key() -> str:
    return os.getenv("PAYSTACK_SECRET_KEY", "")


@router.post("/billing/checkout")
async def checkout(payload: CheckoutIn,
                   user: CurrentUser = Depends(require_roles("Owner")),
                   s: AsyncSession = Depends(_session)):
    plan = ((await s.execute(select(Plan).where(Plan.id == payload.plan_id))).scalars().first())
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if _stripe_key():
        import stripe

        stripe.api_key = _stripe_key()
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price_data": {
                "currency": "usd", "unit_amount": int(plan.monthly_price * 100),
                "recurring": {"interval": "month"},
                "product_data": {"name": plan.name}}, "quantity": 1}],
            success_url=payload.success_url or "http://localhost:3002/?paid=1",
            cancel_url=payload.cancel_url or "http://localhost:3002/?cancelled=1",
            client_reference_id=user.org_id,
            metadata={"org_id": user.org_id, "plan_id": plan.id},
        )
        return {"provider": "stripe", "url": session.url}
    if _paystack_key():
        import httpx

        r = httpx.post(
            "https://api.paystack.co/transaction/initialize",
            headers={"Authorization": f"Bearer {_paystack_key()}"},
            json={"email": user.user_id, "amount": int(plan.monthly_price * 100),
                  "currency": "NGN" if plan.monthly_price < 100 else "USD",
                  "metadata": {"org_id": user.org_id, "plan_id": plan.id},
                  "callback_url": payload.success_url or "http://localhost:3002/?paid=1"},
            timeout=20,
        )
        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"paystack: {r.text[:200]}")
        return {"provider": "paystack", "url": r.json()["data"]["authorization_url"]}
    raise HTTPException(
        status_code=501,
        detail="No billing provider configured — set STRIPE_SECRET_KEY or PAYSTACK_SECRET_KEY",
    )


def verify_paystack_signature(secret: str, body: bytes, signature: str) -> bool:
    digest = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(digest, signature or "")


@router.post("/billing/webhook/paystack")
async def paystack_webhook(request: Request, x_paystack_signature: str = Header(default=""),
                           s: AsyncSession = Depends(_session)):
    body = await request.body()
    if not verify_paystack_signature(_paystack_key() or "unset", body, x_paystack_signature):
        raise HTTPException(status_code=401, detail="bad signature")
    import json as _json

    event = _json.loads(body or b"{}")
    meta = ((event.get("data") or {}).get("metadata") or {})
    org_id = meta.get("org_id", "")
    if event.get("event") == "charge.success" and org_id:
        ent = ((await s.execute(select(Entitlement).where(Entitlement.org_id == org_id)))
               .scalars().first())
        if ent is None:
            ent = Entitlement(org_id=org_id, status="active", plan_id=meta.get("plan_id"))
            s.add(ent)
        else:
            ent.status, ent.plan_id = "active", meta.get("plan_id") or ent.plan_id
        await log_action(s, org_id=org_id, actor="paystack", action="billing.activated",
                         detail={"plan_id": meta.get("plan_id")})
        await s.commit()
        return {"ok": True, "org": org_id}
    return {"ok": True, "ignored": event.get("event")}


@router.post("/billing/webhook/stripe")
async def stripe_webhook(request: Request, stripe_signature: str = Header(default="", alias="Stripe-Signature"),
                         s: AsyncSession = Depends(_session)):
    if not _stripe_key():
        raise HTTPException(status_code=501, detail="STRIPE_SECRET_KEY not set")
    import stripe

    try:
        event = stripe.Webhook.construct_event(
            await request.body(), stripe_signature,
            os.getenv("STRIPE_WEBHOOK_SECRET", ""))
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"bad signature: {exc}")
    if event.get("type") == "checkout.session.completed":
        obj = event.get("data", {}).get("object", {})
        org_id = (obj.get("metadata") or {}).get("org_id", "")
        if org_id:
            ent = ((await s.execute(select(Entitlement).where(Entitlement.org_id == org_id)))
                   .scalars().first())
            if ent is None:
                ent = Entitlement(org_id=org_id, status="active")
                s.add(ent)
            else:
                ent.status = "active"
            await log_action(s, org_id=org_id, actor="stripe", action="billing.activated", detail={})
            await s.commit()
            return {"ok": True, "org": org_id}
    return {"ok": True, "ignored": event.get("type")}


@router.get("/billing/status")
async def billing_status(user: CurrentUser = Depends(get_current_user),
                         s: AsyncSession = Depends(_session)):
    ent = ((await s.execute(select(Entitlement).where(Entitlement.org_id == user.org_id)))
           .scalars().first())
    org = ((await s.execute(select(Organization).where(Organization.id == user.org_id)))
           .scalars().first())
    return {"status": ent.status if ent else "trialing",
            "trial_ends": org.trial_ends.isoformat() if org and org.trial_ends else None,
            "providers": {"stripe": bool(_stripe_key()), "paystack": bool(_paystack_key())}}


@router.get('/billing/plans')
async def list_plans(user: CurrentUser = Depends(get_current_user), s: AsyncSession = Depends(_session)):
    rows = ((await s.execute(select(Plan).where(Plan.id.is_not(None)).limit(50))).scalars().all())
    return [{'id': r.id, 'name': r.name, 'monthly_price': r.monthly_price} for r in rows]

