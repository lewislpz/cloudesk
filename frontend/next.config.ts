import path from "node:path";

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  generateBuildId: async () => process.env.NEXT_BUILD_ID ?? "local",
  output: "standalone",
  outputFileTracingRoot: path.join(process.cwd(), ".."),
};

export default nextConfig;
