import crypto from "crypto";
import { withSentryConfig } from "@sentry/nextjs";

// ── Validation des variables d'environnement critiques en build ──────
const requiredEnvVars = ["NEXT_PUBLIC_API_URL"];
if (process.env.NODE_ENV === "production") {
  for (const envVar of requiredEnvVars) {
    if (!process.env[envVar]) {
      console.warn(
        `⚠ WARNING: ${envVar} is not set. The app will fallback to localhost which won't work in production.`
      );
    }
  }
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  // Unique build ID per deploy — ensures chunk hashes are never stale.
  // Prevents ChunkLoadError when users have cached an old build manifest.
  generateBuildId: async () => {
    return `build-${Date.now()}-${crypto.randomBytes(4).toString("hex")}`;
  },
  async rewrites() {
    const apiUrl = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "";
    const baseUrl = apiUrl.startsWith("http")
      ? apiUrl
      : "http://localhost:8000/api/v1";
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
