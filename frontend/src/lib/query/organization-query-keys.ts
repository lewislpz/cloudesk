import type { OrganizationId } from "@/lib/api/generated";

function organizationRoot(organizationId: OrganizationId) {
  if (!organizationId.trim()) {
    throw new Error("organizationId is required for tenant-scoped query keys.");
  }
  return ["organization", organizationId] as const;
}

export const organizationQueryKeys = {
  root: organizationRoot,
  projects: <TFilters extends Readonly<Record<string, unknown>>>(
    organizationId: OrganizationId,
    filters: TFilters,
  ) => [...organizationRoot(organizationId), "projects", filters] as const,
};
