// Authed FastAPI client. JWT comes from our own /api/auth/token route (same-origin,
// session cookie) so no client-plugin API guessing. Org is the active organization.
const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"; // canonical API (LOCAL_STACK.md)

async function authHeaders(): Promise<Record<string, string>> {
  const tok = await fetch("/api/auth/token");
  if (!tok.ok) throw new Error("Not signed in — please sign in again.");
  const { token } = (await tok.json()) as { token?: string };
  if (!token) throw new Error("No token issued — please sign in again.");
  const sess = await fetch("/api/auth/get-session");
  if (!sess.ok) throw new Error("No active session — please sign in again.");
  const orgId = ((await sess.json()) as { session?: { activeOrganizationId?: string } | null })?.session
    ?.activeOrganizationId;
  if (!orgId) throw new Error("No active organization — create or activate one, then retry.");
  // Role comes from the JWT (org membership); header is a fallback only.
  return { Authorization: `Bearer ${token}`, "X-Org-Id": orgId, "X-Role": "CSR" };
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(await authHeaders()), ...(init?.headers || {}) },
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status}: ${detail.slice(0, 200)}`);
  }
  return (await res.json()) as T;
}

export async function apiForm<T>(path: string, form: FormData): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: await authHeaders(),
    body: form,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status}: ${detail.slice(0, 200)}`);
  }
  return (await res.json()) as T;
}

export type TodayCounts = {
  urgent: number;
  follow_ups: number;
  pending_agents: number;
  awaiting_approval: number;
  exceptions: number;
};

export type Situation = { id: string; status: string; missing: string[]; next_action: string };
