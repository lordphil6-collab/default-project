import { getActiveRole } from "../../../../lib/auth-server";

export async function GET(): Promise<Response> {
  const role = await getActiveRole();
  return Response.json(role ?? { role: null, orgId: null });
}
