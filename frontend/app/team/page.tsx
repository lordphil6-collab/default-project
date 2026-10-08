"use client";
import { useCallback, useEffect, useState } from "react";
import { authClient } from "../../lib/auth-client";
import { ActionButton, Card } from "../../components/primitives";

type Invitation = { id: string; email: string; role: string | null; status: string };

async function activeOrgId(): Promise<string> {
  const sess = await fetch("/api/auth/get-session");
  const orgId = ((await sess.json()) as { session?: { activeOrganizationId?: string } | null })?.session
    ?.activeOrganizationId;
  if (!orgId) throw new Error("No active organization");
  return orgId;
}

export default function Team() {
  const [rows, setRows] = useState<Invitation[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("member");

  const refresh = useCallback(async () => {
    setError("");
    try {
      const orgId = await activeOrgId();
      const res = await authClient.organization.listInvitations({ query: { organizationId: orgId } });
      if (res.error) throw new Error(res.error.message || "Failed");
      setRows(((res.data || []) as Invitation[]).filter((i) => i.status === "pending"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed (Owner/Manager only)");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const orgId = await activeOrgId();
      const res = await authClient.organization.inviteMember({ email, role: role as "owner" | "admin" | "member", organizationId: orgId });
      if (res.error) throw new Error(res.error.message || "Failed");
      setNotice(`Invited ${email} as ${role} ✓ (email sends when SMTP is configured)`);
      setEmail("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Card title="Invite member (Owner/Manager)">
        {error ? <p className="pill red">{error}</p> : null}
        {notice ? <p className="pill green">{notice}</p> : null}
        <form onSubmit={submit} style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <input aria-label="Email" placeholder="teammate@forwarder.com" value={email} onChange={(e) => setEmail(e.target.value)} />
          <select aria-label="Role" value={role} onChange={(e) => setRole(e.target.value)}>
            <option value="member">CSR (member)</option>
            <option value="admin">Manager (admin)</option>
            <option value="owner">Owner</option>
          </select>
          <ActionButton busy={busy} submit>Send invite</ActionButton>
        </form>
        <p className="muted">Owner → app Owner · admin → Manager · member → CSR (enforced by the API from the JWT).</p>
      </Card>
      <Card title={`Pending invitations (${rows.length})`}>
        {rows.map((i) => (
          <p key={i.id} className="muted">
            {i.email} — {i.role} — {i.status} <span className="mono">[{i.id.slice(0, 8)}]</span>
          </p>
        ))}
      </Card>
    </>
  );
}
