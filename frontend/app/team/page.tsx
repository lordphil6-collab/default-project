"use client";
import { useCallback, useEffect, useState } from "react";
import { authClient } from "../../lib/auth-client";
import { ActionButton, Card } from "../../components/primitives";

type Invitation = { id: string; email: string; role: string | null; status: string };
type Member = { id: string; userId: string; role: string; user?: { email?: string; name?: string } };

async function activeOrgId(): Promise<string> {
  const sess = await fetch("/api/auth/get-session");
  const orgId = ((await sess.json()) as { session?: { activeOrganizationId?: string } | null })?.session
    ?.activeOrganizationId;
  if (!orgId) throw new Error("No active organization");
  return orgId;
}

export default function Team() {
  const [rows, setRows] = useState<Invitation[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("member");

  const refresh = useCallback(async () => {
    setError("");
    try {
      const orgId = await activeOrgId();
      const [inv, mem] = await Promise.all([
        authClient.organization.listInvitations({ query: { organizationId: orgId } }),
        authClient.organization.listMembers({ query: { organizationId: orgId } }),
      ]);
      if (inv.error) throw new Error(inv.error.message || "Failed");
      if (mem.error) throw new Error(mem.error.message || "Failed");
      setRows(((inv.data || []) as Invitation[]).filter((i) => i.status === "pending"));
      setMembers((((mem.data as { members?: Member[] } | null)?.members) || []));
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
        {rows.length === 0 && !error ? <p className="muted">No pending invites — new teammates accept from the link in their invitation email, then appear in your company.</p> : null}
        {rows.map((i) => (
          <p key={i.id} className="muted">
            {i.email} — {i.role} — {i.status} <span className="mono">[{i.id.slice(0, 8)}]</span>
          </p>
        ))}
      </Card>
      <Card title={`Members (${members.length})`}>
        {members.length === 0 && !error ? <p className="muted">Just you so far — invite teammates above.</p> : null}
        {members.map((m) => (
          <p key={m.id} className="muted">
            <b>{m.user?.email || m.user?.name || m.userId.slice(0, 8)}</b> — {m.role}{" "}
            <select
              aria-label={`Role for ${m.user?.email || m.userId}`}
              value={m.role}
              onChange={async (e) => {
                setError("");
                try {
                  const orgId = await activeOrgId();
                  const res = await authClient.organization.updateMemberRole({
                    memberId: m.id, role: e.target.value as "owner" | "admin" | "member", organizationId: orgId,
                  });
                  if (res.error) throw new Error(res.error.message || "Failed");
                  setNotice("Role updated ✓");
                  await refresh();
                } catch (err) {
                  setError(err instanceof Error ? err.message : "Failed");
                }
              }}
            >
              <option value="member">CSR (member)</option>
              <option value="admin">Manager (admin)</option>
              <option value="owner">Owner</option>
            </select>{" "}
            <button
              className="btn sec"
              type="button"
              style={{ padding: "2px 8px", fontSize: 12 }}
              onClick={async () => {
                if (!window.confirm(`Remove ${m.user?.email || "this member"} from the company?`)) return;
                setError("");
                try {
                  const orgId = await activeOrgId();
                  const res = await authClient.organization.removeMember({ memberIdOrEmail: m.id, organizationId: orgId });
                  if (res.error) throw new Error(res.error.message || "Failed");
                  setNotice("Member removed ✓");
                  await refresh();
                } catch (err) {
                  setError(err instanceof Error ? err.message : "Failed");
                }
              }}
            >
              Remove
            </button>
          </p>
        ))}
      </Card>
    </>
  );
}
