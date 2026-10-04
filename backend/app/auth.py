"""Better Auth guard with real JWKS verification (Phase 8 hardening).

Contract: Next.js (Better Auth) sends `Authorization: Bearer <jwt>`
+ `X-Org-Id` + `X-Role`. FastAPI enforces org scoping on every query.

Modes:
- Dev/pilot default: ALLOW_AUTH_STUB=true → any Bearer token accepted, org/role
  taken from headers (previous phases' behavior). No network needed.
- Prod: ALLOW_AUTH_STUB=false + FASTAPI_JWKS_URL set → JWT signature verified
  against the JWKS, and the token's org claim must match X-Org-Id.
"""
import os
import time

import httpx
from fastapi import Depends, Header, HTTPException
from jwt.algorithms import ECAlgorithm, OKPAlgorithm, RSAAlgorithm
from jwt import PyJWT


class CurrentUser:
    def __init__(self, user_id: str, org_id: str, role: str):
        self.user_id = user_id
        self.org_id = org_id
        self.role = role


_jwks_cache: dict = {"keys": None, "fetched_at": 0.0}
_JWKS_TTL_S = 600.0


def stub_allowed() -> bool:
    return os.getenv("ALLOW_AUTH_STUB", "true").lower() == "true"


def jwks_url() -> str:
    return os.getenv("FASTAPI_JWKS_URL", "")


async def _get_jwks_keys() -> list:
    now = time.time()
    if _jwks_cache["keys"] is not None and now - _jwks_cache["fetched_at"] < _JWKS_TTL_S:
        return _jwks_cache["keys"]
    url = jwks_url()
    if not url:
        raise HTTPException(status_code=500, detail="FASTAPI_JWKS_URL not configured")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            keys = resp.json().get("keys", [])
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"JWKS fetch failed: {exc}")
    _jwks_cache.update(keys=keys, fetched_at=now)
    return keys


async def verify_token(token: str) -> dict:
    """Verify JWT signature against the JWKS. Returns claims. Raises 401 on failure."""
    import json

    decoder = PyJWT()
    last_err = "no keys"
    for jwk in await _get_jwks_keys():
        try:
            if isinstance(jwk, str):
                key: object = jwk  # raw HMAC secret (tests)
            elif jwk.get("kty") == "OKP":
                key = OKPAlgorithm.from_jwk(json.dumps(jwk))
            elif jwk.get("kty") == "EC":
                key = ECAlgorithm.from_jwk(json.dumps(jwk))
            elif jwk.get("kty") == "RSA":
                key = RSAAlgorithm.from_jwk(json.dumps(jwk))
            elif jwk.get("kty") == "oct":
                key = jwk["k"]
            else:
                last_err = f"unsupported kty: {jwk.get('kty')}"
                continue
            return decoder.decode(
                token, key,  # type: ignore[arg-type]
                algorithms=["EdDSA", "ES256", "RS256", "HS256"],
                options={"verify_aud": False},
            )
        except Exception as exc:
            last_err = str(exc)
    raise HTTPException(status_code=401, detail=f"Invalid token: {last_err}")


async def get_current_user(
    authorization: str = Header(default=""),
    x_org_id: str = Header(default="", alias="X-Org-Id"),
    x_role: str = Header(default="CSR", alias="X-Role"),
) -> CurrentUser:
    if not authorization.startswith("Bearer ") or not x_org_id:
        raise HTTPException(status_code=401, detail="Missing Bearer token or X-Org-Id")
    token = authorization[len("Bearer "):]
    if stub_allowed():
        return CurrentUser(user_id="stub-user", org_id=x_org_id, role=x_role)
    claims = await verify_token(token)
    token_org = claims.get("org_id") or claims.get("orgId") or claims.get("organizationId")
    if not token_org:
        raise HTTPException(status_code=401, detail="Token carries no organization")
    if token_org != x_org_id:
        raise HTTPException(status_code=403, detail="Token org does not match X-Org-Id")
    user_id = str(claims.get("sub", "unknown"))
    role = str(claims.get("role", x_role))
    return CurrentUser(user_id=user_id, org_id=x_org_id, role=role)


def require_roles(*allowed: str):
    async def guard(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail="Forbidden for role")
        return user

    return guard
