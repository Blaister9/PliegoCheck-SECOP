import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["@pliegocheck/schemas"],
};

export default nextConfig;
