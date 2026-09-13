/** @type {import('next').NextConfig} */
const nextConfig = {
  /**
   * Proxy /api/v1/* → Render backend at CDN/infrastructure level.
   * This runs on Vercel's edge (no 10s serverless timeout), handles
   * cold-starts gracefully, and completely eliminates browser CORS.
   */
  async rewrites() {
    const backendUrl =
      process.env.BACKEND_INTERNAL_URL ||
      "https://akmmotion-backend.onrender.com";
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendUrl}/api/v1/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
