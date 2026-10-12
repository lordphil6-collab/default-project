import { createAuthClient } from "better-auth/react";
import { organizationClient } from "better-auth/client/plugins";

export const authClient = createAuthClient({
  // Same-origin by default so the app works on any port (3000/3002).
  // Set NEXT_PUBLIC_BETTER_AUTH_URL only when the auth server differs.
  baseURL: process.env.NEXT_PUBLIC_BETTER_AUTH_URL || undefined,
  plugins: [organizationClient()],
});
