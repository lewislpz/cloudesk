import Link from "next/link";
import type { ReactNode } from "react";

import { Brand } from "@/components/brand";

const workspaceSections = [
  "Clientes",
  "Proyectos",
  "Tiempo",
  "Facturación",
] as const;

type WorkspaceShellProps = Readonly<{
  children: ReactNode;
  organizationName: string;
  organizationSlug: string;
}>;

export function WorkspaceShell({
  children,
  organizationName,
  organizationSlug,
}: WorkspaceShellProps) {
  const workspaceHref = `/${encodeURIComponent(organizationSlug)}`;

  return (
    <div className="min-h-screen bg-canvas lg:grid lg:grid-cols-[17rem_1fr]">
      <aside className="border-b border-line bg-surface px-5 py-5 lg:min-h-screen lg:border-b-0 lg:border-r lg:px-6">
        <div className="flex items-center justify-between lg:block">
          <Brand />
          <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-brand lg:hidden">
            {organizationName}
          </span>
        </div>
        <div className="mt-8 hidden lg:block">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-muted">
            Organización
          </p>
          <p className="mt-2 truncate font-semibold">{organizationName}</p>
        </div>
        <nav aria-label="Espacio de trabajo" className="mt-5 lg:mt-10">
          <ul className="flex gap-2 overflow-x-auto pb-1 lg:block lg:space-y-1">
            <li>
              <Link
                aria-current="page"
                className="inline-flex min-h-11 min-w-max items-center rounded-xl bg-ink px-4 text-sm font-semibold text-white lg:flex"
                href={workspaceHref}
              >
                Resumen
              </Link>
            </li>
            {workspaceSections.map((section) => (
              <li
                className="inline-flex min-h-11 min-w-max items-center rounded-xl px-4 text-sm font-medium text-muted lg:flex"
                key={section}
              >
                {section}
                <span className="sr-only">, próximamente</span>
              </li>
            ))}
          </ul>
        </nav>
        <p className="mt-8 hidden border-t border-line pt-5 text-xs leading-5 text-muted lg:block">
          La sesión segura del servidor protegerá este shell en el siguiente
          vertical.
        </p>
      </aside>

      <div className="min-w-0">
        <header className="flex min-h-20 items-center justify-between border-b border-line bg-surface px-5 sm:px-8 lg:px-10">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.14em] text-muted">
              Espacio activo
            </p>
            <p className="mt-1 font-semibold lg:hidden">{organizationName}</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-muted sm:inline">
              Shell autenticado
            </span>
            <span
              aria-label="Perfil de ejemplo"
              className="grid size-10 place-items-center rounded-full bg-amber-100 text-sm font-bold text-amber-950"
              role="img"
            >
              LS
            </span>
          </div>
        </header>
        <main className="px-5 py-8 sm:px-8 lg:px-10 lg:py-10" id="main-content">
          {children}
        </main>
      </div>
    </div>
  );
}
