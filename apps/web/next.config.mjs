import { withSentryConfig } from "@sentry/nextjs";

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  async rewrites() {
    const apiUrl = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "";
    const baseUrl = apiUrl.startsWith("http")
      ? apiUrl
      : "https://ao-copilot-production.up.railway.app/api/v1";
    return [
      {
        source: "/api/v1/:path*",
        destination: `${baseUrl}/:path*`,
      },
    ];
  },
};

export default withSentryConfig(nextConfig, {
  // Suppresses source map upload logs during build
  silent: true,
  // Upload source maps only when SENTRY_AUTH_TOKEN is set
  org: process.env.SENTRY_ORG || "",
  project: process.env.SENTRY_PROJECT || "",
  // Disable source map upload in CI without token
  disableServerWebpackPlugin: !process.env.SENTRY_AUTH_TOKEN,
  disableClientWebpackPlugin: !process.env.SENTRY_AUTH_TOKEN,
});
