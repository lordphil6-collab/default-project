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

export function friendlyError(raw: string): string {
  const msg = raw || "Request failed";
  if (/^401:/.test(msg)) {
    if (/X-Org-Id|Bearer/i.test(msg)) return "Not signed in — please sign in again.";
    return "Your session expired — please sign in again.";
  }
  if (/^402:/.test(msg)) return "Trial expired — open Billing to subscribe and keep working.";
  if (/^403:/.test(msg)) {
    if (/role|Forbidden/i.test(msg)) return "Your role can't do that — ask an Owner or Manager.";
    return "Wrong workspace — switch companies in the top bar and retry.";
  }
  if (/^404:/.test(msg)) return "Not found in your workspace — it may belong to another company.";
  if (/^409:/.test(msg)) return msg.replace(/^409:\s*/, "") || "That action isn't allowed right now.";
  if (/^422:/.test(msg)) return msg.replace(/^422:\s*/, "") || "Something's missing — check the form and retry.";
  if (/No active organization/i.test(msg))
    return "No active company — pick one in the top bar or create it from Signup.";
  if (/Failed to fetch|Unable to connect|NetworkError/i.test(msg))
    return "Can't reach the server — is the API running on :8000?";
  return msg.length > 220 ? `${msg.slice(0, 220)}…` : msg;
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(await authHeaders()), ...(init?.headers || {}) },
  }).catch(() => {
    throw new Error("Can't reach the server — is the API running on :8000?");
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(friendlyError(`${res.status}: ${detail.slice(0, 200)}`));
  }
  return (await res.json()) as T;
}

export async function apiForm<T>(path: string, form: FormData): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: await authHeaders(),
    body: form,
  }).catch(() => {
    throw new Error("Can't reach the server — is the API running on :8000?");
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(friendlyError(`${res.status}: ${detail.slice(0, 200)}`));
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

export type Situation = { id: string; status: string; missing: string[]; next_action: string; origin?: string; destination?: string; mode?: string };
