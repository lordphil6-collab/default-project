"use client";
import { useState } from "react";
import { authClient } from "../../lib/auth-client";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const res = await authClient.signIn.email({ email, password });
    if (res.error) setError(res.error.message || "Sign in failed");
    else window.location.href = "/";
  }

  return (
    <div className="card" style={{ maxWidth: 420 }}>
      <h2 style={{ fontSize: 15, margin: "4px 0 8px" }}>Sign in</h2>
      <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        <input aria-label="Email" placeholder="you@forwarder.com" value={email} onChange={(e) => setEmail(e.target.value)} />
        <input aria-label="Password" type="password" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} />
        {error ? <p className="pill red">{error}</p> : null}
        <button className="btn" type="submit">Sign in</button>
      </form>
      <p className="muted">New company? <a href="/signup">Create account + trial</a> — your owner creates the organization, then invites you. Trial starts on signup.</p>
    </div>
  );
}
