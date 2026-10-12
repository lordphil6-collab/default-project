"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { authClient } from "../../lib/auth-client";

function slugify(name: string): string {
  const base = name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 40) || "company";
  return `${base}-${Date.now().toString(36)}`;
}

export default function Signup() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [org, setOrg] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    const trimmedName = name.trim();
    const trimmedEmail = email.trim();
    if (!trimmedName) return setError("Please enter your name.");
    if (!trimmedEmail || !/^\S+@\S+\.\S+$/.test(trimmedEmail))
      return setError("Please enter a valid email address.");
    if (password.length < 8) return setError("Password must be at least 8 characters.");

    setLoading(true);
    try {
      const up = await authClient.signUp.email({
        name: trimmedName,
        email: trimmedEmail,
        password,
      });
      if (up.error) throw new Error(up.error.message || "Sign up failed");
      const company = org.trim() || `${trimmedName}'s company`;
      const created = await authClient.organization.create({
        name: company,
        slug: slugify(company),
      });
      if (created.error) throw new Error(created.error.message || "Organization failed");
      const orgId =
        (created.data as { id?: string } | null)?.id ??
        (created.data as { organization?: { id?: string } } | null)?.organization?.id;
      if (!orgId) throw new Error("No organization id returned");
      const active = await authClient.organization.setActive({ organizationId: orgId });
      if (active.error) throw new Error(active.error.message || "Could not activate organization");
      router.push("/");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign up failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card" style={{ maxWidth: 440 }}>
      <h2 style={{ fontSize: 15, margin: "4px 0 8px" }}>Create account + trial</h2>
      <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        <input aria-label="Your name" placeholder="Adaeze Okonkwo" value={name} onChange={(e) => setName(e.target.value)} required autoComplete="name" />
        <input aria-label="Company" placeholder="Acme Forwarders" value={org} onChange={(e) => setOrg(e.target.value)} autoComplete="organization" />
        <input aria-label="Email" placeholder="you@forwarder.com" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
        <input aria-label="Password" type="password" placeholder="8+ characters" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} autoComplete="new-password" />
        {error ? <p className="pill red">{error}</p> : null}
        <button className="btn" type="submit" disabled={loading}>{loading ? "Creating account…" : "Start 30-day trial"}</button>
      </form>
      <p className="muted">Creates your login and your company workspace. Already have one? <a href="/login">Sign in</a>.</p>
    </div>
  );
}
