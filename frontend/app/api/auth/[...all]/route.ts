import { auth } from "../../../../lib/auth-server";

export async function GET(request: Request): Promise<Response> {
  return auth.handler(request);
}

export async function POST(request: Request): Promise<Response> {
  return auth.handler(request);
}
