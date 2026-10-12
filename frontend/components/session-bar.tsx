import { headers } from "next/headers";
import { auth, getActiveRole } from "../lib/auth-server";
import { StatusPill } from "./primitives";
import { LogoutButton } from "./logout-button";
import { OrgSwitcher } from "./org-switcher";
import { TrialPill } from "./trial-pill";

export async function SessionBar() {
  let email: string | null = null;
  let role: string | null = null;
  try {
    const session = await auth.api.getSession({ headers: await headers() });
    email = session?.user?.email ?? null;
    if (email) role = (await getActiveRole())?.role ?? null;
  } catch (err) {
    console.error("[SessionBar] getSession failed:", err);
    email = null;
  }
  if (!email) {
    return (
      <a className="pill indigo" href="/login" style={{ textDecoration: "none" }}>
        Sign in
      </a>
    );
  }
  return (
    <>
      <OrgSwitcher />
      {role ? (
        <span className="pill indigo" title="Your role in the active company — gates approvals and admin">
          {role}
        </span>
      ) : null}
      <span className="pill green" title={email}>
        {email.length > 22 ? `${email.slice(0, 22)}…` : email}
      </span>
      <LogoutButton />
    </>
  );
}

export { TrialPill };
