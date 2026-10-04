import { defineConfig } from "drizzle-kit";

// Pushes frontend/drizzle/auth-schema.ts (Better Auth tables) to Postgres.
// Needs live DATABASE_URL, e.g. the pgserver URL in .pg_url (pilot dev).
export default defineConfig({
  schema: "./drizzle/auth-schema.ts",
  dialect: "postgresql",
  dbCredentials: {
    url:
      process.env.DATABASE_URL?.replace("postgresql+asyncpg://", "postgresql://") ||
      "postgresql://postgres:postgres@localhost:5432/quote_desk",
  },
});
