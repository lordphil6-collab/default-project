import { headers } from "next/headers";
import { auth } from "../lib/auth-server";
import { StatusPill } from "./primitives";
import { LogoutButton } from "./logout-button";
import { RoleSelect } from "./role-select";

export async function SessionBar() {
  let email: string | null = null;
  try {
    const session = await auth.api.getSession({ headers: await headers() });
    email = session?.user?.email ?? null;
  } catch {
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
      <span className="pill green" title={email}>
        {email.length > 22 ? `${email.slice(0, 22)}…` : email}
      </span>
      <RoleSelect />
      <LogoutButton />
    </>
  );
}

export function TrialPill() {
  return <StatusPill tone="indigo">Trial</StatusPill>;
}
