import { NextRequest, NextResponse } from "next/server";

/**
 * Next.js Edge Middleware — auth guard for protected routes.
 *
 * Checks for the presence of an access_token cookie before allowing
 * access to dashboard routes. This prevents the "flash of unauthenticated
 * content" that happens with client-side-only auth checks.
 *
 * NOTE: This only checks cookie presence, not JWT validity.
 * The backend validates the token on every API call.
 */

const PUBLIC_PATHS = [
  "/",
  "/login",
  "/register",
  "/pricing",
  "/legal",
  "/ai-transparency",
  "/status",
  "/api",
  "/_next",
  "/favicon",
  "/icons",
  "/manifest.json",
  "/robots.txt",
  "/sitemap.xml",
];

function isPublicPath(pathname: string): boolean {
  return PUBLIC_PATHS.some(
    (p) => pathname === p || pathname.startsWith(p + "/") || pathname.startsWith(p + ".")
  );
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public paths
  if (isPublicPath(pathname)) {
    return NextResponse.next();
  }

  // Allow static assets
  if (
    pathname.includes(".") ||
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api")
  ) {
    return NextResponse.next();
  }

  // Check for auth token (cookie or localStorage-backed)
  const token =
    request.cookies.get("access_token")?.value ||
    request.cookies.get("ao_token")?.value;

  if (!token) {
    // Redirect to login with return URL
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  // Match all routes except static files and API routes
  matcher: [
    "/((?!_next/static|_next/image|favicon\\.ico|icons|manifest\\.json|robots\\.txt|sitemap\\.xml).*)",
  ],
};
