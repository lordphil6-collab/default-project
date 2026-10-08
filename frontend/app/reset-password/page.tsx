"use client";
import { useState } from "react";
import { authClient } from "../../lib/auth-client";
import { Card } from "../../components/primitives";

export default function ResetPassword() {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const token = new URLSearchParams(window.location.search).get("token") || "";
    const res = await authClient.resetPassword({ newPassword: password, token });
    if (res.error) setError(res.error.message || "Failed");
    else {
      setDone(true);
      window.location.href = "/login";
    }
  }

  return (
    <Card title="Set new password">
      {error ? <p className="pill red">{error}</p> : null}
      <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        <input aria-label="New password" type="password" placeholder="8+ characters" value={password} onChange={(e) => setPassword(e.target.value)} />
        <p>
          <button className="btn" type="submit">Save password</button>
        </p>
      </form>
      {done ? <p className="pill green">Saved ✓ redirecting…</p> : null}
    </Card>
  );
}
