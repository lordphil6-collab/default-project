"use client";
import { useEffect, useState } from "react";
import { authClient } from "../lib/auth-client";

type Org = { id: string; name: string };

// Always-visible org switcher: shows the active company, lets you switch or
// create one. Without an active org every API call fails, so this must never
// be a dead end.
export function OrgSwitcher() {
  const [orgs, setOrgs] = useState<Org[]>([]);
  const [activeId, setActiveId] = useState<string>("");
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const sess = await fetch("/api/auth/get-session");
        const active = ((await sess.json()) as { session?: { activeOrganizationId?: string } | null })?.session
          ?.activeOrganizationId;
        setActiveId(active || "");
        const res = await fetch("/api/auth/organization/list");
        if (!res.ok) throw new Error("Failed");
        const body = (await res.json()) as Org[] | { organizations?: Org[] } | null;
        const list = Array.isArray(body) ? body : body?.organizations || [];
        setOrgs(list.filter((o) => o && o.id));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed");
      }
    })();
  }, []);

  async function change(id: string) {
    if (!id || id === activeId) return;
    setError("");
    const res = await authClient.organization.setActive({ organizationId: id });
    if (res.error) setError(res.error.message || "Failed");
    else window.location.reload();
  }

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const slug = `${name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40)}-${Date.now().toString(36)}`;
      const res = await authClient.organization.create({ name, slug });
      if (res.error) throw new Error(res.error.message || "Failed");
      const id = (res.data as { id?: string } | null)?.id;
      if (!id) throw new Error("No organization id returned");
      const active = await authClient.organization.setActive({ organizationId: id });
      if (active.error) throw new Error(active.error.message || "Failed");
      window.location.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setCreating(false);
    }
  }

  return (
    <span style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
      <select
        aria-label="Active company"
        value={activeId}
        onChange={(e) => (e.target.value === "__new" ? setCreating(true) : change(e.target.value))}
        title={error || "Active company — everything is scoped to it"}
      >
        {activeId === "" ? <option value="">No company — pick one</option> : null}
        {orgs.map((o) => (
          <option key={o.id} value={o.id}>
            {o.name}
          </option>
        ))}
        <option value="__new">＋ New company…</option>
      </select>
      {creating ? (
        <form onSubmit={create} style={{ display: "inline-flex", gap: 4 }}>
          <input aria-label="Company name" placeholder="Company" value={name} onChange={(e) => setName(e.target.value)} style={{ width: 140 }} />
          <button className="btn sec" type="submit" style={{ padding: "4px 10px", fontSize: 13 }}>
            Create
          </button>
        </form>
      ) : null}
    </span>
  );
}
