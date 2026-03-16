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

export default nextConfig;
