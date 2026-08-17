import { fileURLToPath } from "node:url";

import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: {
      "@branchlab/reference-world": fileURLToPath(
        new URL("./packages/reference-world/src/index.ts", import.meta.url),
      ),
      "@branchlab/schemas": fileURLToPath(
        new URL("./packages/schemas/src/index.ts", import.meta.url),
      ),
      "@branchlab/simulation-core": fileURLToPath(
        new URL("./packages/simulation-core/src/index.ts", import.meta.url),
      ),
      "@branchlab/gtfs-importer": fileURLToPath(
        new URL("./packages/gtfs-importer/src/index.ts", import.meta.url),
      ),
    },
  },
  test: {
    include: ["packages/**/*.test.ts", "apps/**/*.test.ts"],
    passWithNoTests: false,
  },
});
