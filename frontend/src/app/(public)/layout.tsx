import type { ReactNode } from "react";

import { Brand } from "@/components/brand";

export default function PublicLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <div className="min-h-screen bg-canvas">
      <header className="mx-auto flex max-w-7xl items-center justify-between px-5 py-5 sm:px-8 lg:px-12">
        <Brand />
        <nav
          aria-label="Navegación principal"
          className="flex items-center gap-2 sm:gap-4"
        >
          <a
            className="hidden min-h-11 items-center rounded-full px-4 text-sm font-semibold text-muted hover:text-ink sm:inline-flex"
            href="/demo"
          >
            Ver espacio
          </a>
          <a
            className="inline-flex min-h-11 items-center rounded-full bg-ink px-5 text-sm font-semibold text-white hover:bg-brand-strong"
            href="/onboarding"
          >
            Empezar
          </a>
        </nav>
      </header>
      <main id="main-content">{children}</main>
      <footer className="mx-auto flex max-w-7xl flex-col gap-2 border-t border-line px-5 py-8 text-sm text-muted sm:flex-row sm:items-center sm:justify-between sm:px-8 lg:px-12">
        <p>ClouDesk · trabajo claro, de principio a cobro.</p>
        <p>Base local M0</p>
      </footer>
    </div>
  );
}
