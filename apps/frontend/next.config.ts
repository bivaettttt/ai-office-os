import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: [
    "@ai-office/types",
    "@ai-office/protocol",
    "@ai-office/config",
  ],
};

export default nextConfig;
