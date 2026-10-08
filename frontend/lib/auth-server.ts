// Better Auth server — org = company tenancy, JWT plugin feeds FastAPI JWKS.
import { and, eq } from "drizzle-orm";
import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { jwt } from "better-auth/plugins/jwt";
import { organization } from "better-auth/plugins/organization";
import { member } from "../drizzle/auth-schema";
import { db } from "./db";
import { sendAppEmail } from "./mailer";

// Better Auth org roles -> app roles enforced by FastAPI require_roles.
function mapRole(role: string | null | undefined): string {
  if (role === "owner") return "Owner";
  if (role === "admin") return "Manager";
  return "CSR";
}

async function memberRole(organizationId: string, userId: string): Promise<string> {
  const rows = await db
    .select({ role: member.role })
    .from(member)
    .where(and(eq(member.organizationId, organizationId), eq(member.userId, userId)))
    .limit(1);
  return mapRole(rows[0]?.role);
}

export const auth = betterAuth({
  baseURL: process.env.BETTER_AUTH_URL || "http://localhost:3000",
  secret: process.env.BETTER_AUTH_SECRET || "dev-only-change-me",
  database: drizzleAdapter(db, { provider: "pg" }),
  emailAndPassword: {
    enabled: true,
    sendResetPassword: async ({ user, url }) => {
      await sendAppEmail(user.email, "Reset your password",
        `<p>Reset your Freight Customer Service Desk password:</p><p><a href="${url}">${url}</a></p>`);
    },
  },
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
    organization({
      sendInvitationEmail: async ({ email, invitation }) => {
        const url = `${process.env.BETTER_AUTH_URL || "http://localhost:3000"}/accept?invitationId=${invitation.id}`;
        await sendAppEmail(email, "You're invited",
          `<p>You were invited as <b>${invitation.role}</b>. Accept here:</p><p><a href="${url}">${url}</a></p>`);
      },
    }),
    jwt({
      jwt: {
        // Propagate org + mapped role so FastAPI enforces scoping and gates.
        definePayload: async ({ session }) => {
          const orgId = (session as Record<string, unknown>).activeOrganizationId as string | undefined;
          if (!orgId) return {};
          const userId = (session as { userId?: string }).userId || "";
          return { organizationId: orgId, role: await memberRole(orgId, userId) };
        },
      },
    }),
  ],
});
