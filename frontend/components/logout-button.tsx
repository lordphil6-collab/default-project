"use client";
import { authClient } from "../lib/auth-client";

export function LogoutButton() {
  async function logout() {
    await authClient.signOut({
      fetchOptions: {
        onSuccess: () => {
          window.location.href = "/login";
        },
      },
    });
  }
  return (
    <button className="btn sec" type="button" onClick={logout} style={{ padding: "4px 10px", fontSize: 13 }}>
      Sign out
    </button>
  );
}
