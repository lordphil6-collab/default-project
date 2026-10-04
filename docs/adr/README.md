# ADR-001 Modular monolith first
- Single FastAPI + Next.js. Contexts map to 6 PRD modules.
- Split only on proven pain.
# ADR-002 Better Auth (free, no per-user fee)
- Better Auth in Next.js, shared Postgres, org = company.
- FastAPI verifies JWT via JWKS. See v4 Table 3.
# ADR-003 Free-first stack
- Postgres/Redis/MinIO self-hosted Docker. OSS parsers first.
- Cloudflare R2 free tier prod. Single VPS. See v4 Table 2.
