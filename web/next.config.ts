import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.GETWAY_API_INTERNAL_URL || "http://api:8000"}/:path*`,
      },
    ];
  },
};

export default nextConfig;
