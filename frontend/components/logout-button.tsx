"use client";
import { useRouter } from "next/navigation";
import { authClient } from "../lib/auth-client";

export function LogoutButton() {
  const router = useRouter();
  async function logout() {
    await authClient.signOut({
      fetchOptions: {
        onSuccess: () => {
          router.push("/login");
          router.refresh();
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
