import { describe, expect, it } from "vitest";

import { organizationQueryKeys } from "@/lib/query/organization-query-keys";
import { createQueryClient } from "@/lib/query/create-query-client";

describe("organizationQueryKeys", () => {
  it("starts every tenant key with immutable organization context", () => {
    expect(
      organizationQueryKeys.projects("org-a", { status: "active" }),
    ).toEqual(["organization", "org-a", "projects", { status: "active" }]);
    expect(
      organizationQueryKeys.projects("org-b", { status: "active" }),
    ).not.toEqual(
      organizationQueryKeys.projects("org-a", { status: "active" }),
    );
  });

  it("rejects a missing tenant identifier", () => {
    expect(() => organizationQueryKeys.root(" ")).toThrow(
      /organizationId is required/i,
    );
  });

  it("creates an isolated cache for each runtime", () => {
    expect(createQueryClient()).not.toBe(createQueryClient());
  });
});
