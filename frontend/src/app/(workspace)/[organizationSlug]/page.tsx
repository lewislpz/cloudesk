import { StatusPanel } from "@/components/ui/status-panel";
import { formatOrganizationSlug } from "@/lib/organizations/format-organization-slug";

type WorkspacePageProps = Readonly<{
  params: Promise<{ organizationSlug: string }>;
}>;

export default async function WorkspacePage({ params }: WorkspacePageProps) {
  const { organizationSlug } = await params;
  const name = formatOrganizationSlug(organizationSlug) || "tu organización";

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-8 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-bold uppercase tracking-[0.16em] text-brand">
            Resumen
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
            Panel de {name}
          </h1>
          <p className="mt-3 max-w-2xl leading-7 text-muted">
            La estructura ya está lista para recibir datos generados desde el
            contrato OpenAPI sin mezclar organizaciones.
          </p>
        </div>
        <span className="inline-flex w-fit rounded-full border border-line bg-surface px-4 py-2 text-sm font-semibold text-muted">
          Sin datos conectados
        </span>
      </div>

      <StatusPanel
        description="El primer vertical conectará identidad, organización y proyecto sobre esta base. Hasta entonces, el shell no simula datos de negocio."
        title="Tu espacio está preparado"
        tone="empty"
      />
    </div>
  );
}
