import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    turbo: {
      rules: {
        '*.svg': {
          loaders: ['@svgr/webpack'],
          as: '*.js',
        },
      },
    },
  },
  // Ensure we can connect to the Python server
  async rewrites() {
    return [
      {
        source: '/api/python/:path*',
        destination: 'http://localhost:7860/:path*',
      },
    ];
  },
};

export default nextConfig;
