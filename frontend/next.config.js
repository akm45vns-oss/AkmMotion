/** @type {import('next').NextConfig} */
const nextConfig = {
  /**
   * Disable public browser source maps in production for defense-in-depth.
   */
  productionBrowserSourceMaps: false,

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

  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
          {
            key: "X-XSS-Protection",
            value: "1; mode=block",
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
