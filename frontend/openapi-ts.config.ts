import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  input: "../backend/api/openapi.yaml",
  output: {
    path: process.env.OPENAPI_TS_OUTPUT ?? "src/lib/api/generated",
    postProcess: ["prettier"],
  },
  plugins: [
    "@hey-api/typescript",
    {
      name: "@hey-api/client-fetch",
      throwOnError: true,
    },
    {
      name: "@hey-api/sdk",
      auth: false,
    },
  ],
});
