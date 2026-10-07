"""Clear stale JWKS keys (needed after BETTER_AUTH_SECRET rotation).

The jwt plugin encrypts its Ed25519 keypair with the secret; after rotation
the old rows can't be decrypted and /api/auth/token 500s. Keys regenerate
on the next token request.
"""
import asyncio
import os

import asyncpg

URL = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")


async def main() -> None:
    conn = await asyncpg.connect(URL)
    n = await conn.execute("DELETE FROM jwks")
    print("cleared:", n)
    await conn.close()


asyncio.run(main())
