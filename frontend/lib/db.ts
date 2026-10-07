// Lazy Postgres pool — no connection at import, so `next build` never touches the DB.
import { Pool } from "pg";
import { drizzle } from "drizzle-orm/node-postgres";
import * as schema from "../drizzle/auth-schema";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL?.replace("postgresql+asyncpg://", "postgresql://"),
});

export const db = drizzle(pool, { schema });
