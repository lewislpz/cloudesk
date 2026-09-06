import type { ReactNode } from "react";

import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { RuntimeProvider } from "@/lib/api/runtime/runtime-provider";
import { formatOrganizationSlug } from "@/lib/organizations/format-organization-slug";

type WorkspaceLayoutProps = Readonly<{
  children: ReactNode;
  params: Promise<{ organizationSlug: string }>;
}>;

export default async function WorkspaceLayout({
  children,
  params,
}: WorkspaceLayoutProps) {
  const { organizationSlug } = await params;

  return (
    <RuntimeProvider apiBaseUrl="/">
      <WorkspaceShell
        organizationName={
          formatOrganizationSlug(organizationSlug) || "Organización"
        }
        organizationSlug={organizationSlug}
      >
        {children}
      </WorkspaceShell>
    </RuntimeProvider>
  );
}
