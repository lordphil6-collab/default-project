"use client";
import { useState } from "react";
import { authClient } from "../../lib/auth-client";
import { Card } from "../../components/primitives";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const res = await authClient.requestPasswordReset({ email, redirectTo: "/reset-password" });
    if (res.error) setError(res.error.message || "Failed");
    else setDone(true);
  }

  return (
    <Card title="Forgot password">
      {done ? (
        <p className="muted">If that email exists, a reset link is on its way (check server log in dev).</p>
      ) : (
        <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {error ? <p className="pill red">{error}</p> : null}
          <input aria-label="Email" placeholder="you@forwarder.com" value={email} onChange={(e) => setEmail(e.target.value)} />
          <p>
            <button className="btn" type="submit">Send reset link</button>
          </p>
        </form>
      )}
    </Card>
  );
}
