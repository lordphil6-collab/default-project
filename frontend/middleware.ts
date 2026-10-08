import { NextRequest, NextResponse } from "next/server";

// Edge-safe: checks the session cookie only. Deep auth is enforced by FastAPI.
const PUBLIC = ["/login", "/signup", "/forgot-password", "/reset-password", "/track", "/design-system", "/api/auth"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (PUBLIC.some((p) => pathname === p || pathname.startsWith(p + "/"))) return NextResponse.next();
  const session = request.cookies.get("better-auth.session_token")?.value;
  if (!session) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = { matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"] };
