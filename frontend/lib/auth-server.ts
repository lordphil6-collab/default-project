// Better Auth server — org = company tenancy, JWT plugin feeds FastAPI JWKS.
import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { jwt } from "better-auth/plugins/jwt";
import { organization } from "better-auth/plugins/organization";
import { db } from "./db";

export const auth = betterAuth({
  baseURL: process.env.BETTER_AUTH_URL || "http://localhost:3000",
  secret: process.env.BETTER_AUTH_SECRET || "dev-only-change-me",
  database: drizzleAdapter(db, { provider: "pg" }),
  emailAndPassword: { enabled: true },
  socialProviders: {
    ...(process.env.GOOGLE_CLIENT_ID
      ? { google: { clientId: process.env.GOOGLE_CLIENT_ID, clientSecret: process.env.GOOGLE_CLIENT_SECRET || "" } }
      : {}),
    ...(process.env.MICROSOFT_CLIENT_ID
      ? {
          microsoft: {
            clientId: process.env.MICROSOFT_CLIENT_ID,
            clientSecret: process.env.MICROSOFT_CLIENT_SECRET || "",
          },
        }
      : {}),
  },
  plugins: [
    organization(),
    jwt({
      jwt: {
        // Propagate Better Auth's active organization so FastAPI can enforce org scoping.
        definePayload: ({ session }) => {
          const orgId = (session as Record<string, unknown>).activeOrganizationId;
          return orgId ? { organizationId: orgId } : {};
        },
      },
    }),
  ],
});
