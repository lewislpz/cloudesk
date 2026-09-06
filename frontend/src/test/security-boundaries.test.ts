// @vitest-environment node

import { readFile, readdir } from "node:fs/promises";
import { extname, join } from "node:path";

import { describe, expect, it } from "vitest";

async function sourceFiles(directory: string): Promise<string[]> {
  const entries = await readdir(directory, { withFileTypes: true });
  const nested = await Promise.all(
    entries.map(async (entry) => {
      const path = join(directory, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === "generated" || entry.name === "test") return [];
        return sourceFiles(path);
      }
      return [".ts", ".tsx"].includes(extname(path)) ? [path] : [];
    }),
  );
  return nested.flat();
}

describe("frontend security boundaries", () => {
  it("does not persist credentials or query data in browser storage", async () => {
    const files = await sourceFiles(join(process.cwd(), "src"));
    const sources = await Promise.all(
      files.map((file) => readFile(file, "utf8")),
    );
    const browserStorage = new RegExp(
      ["local", "session"].map((kind) => `${kind}Storage`).join("|"),
    );

    expect(sources.join("\n")).not.toMatch(browserStorage);
  });
});
