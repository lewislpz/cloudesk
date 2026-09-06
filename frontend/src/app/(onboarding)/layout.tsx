import type { ReactNode } from "react";

import { Brand } from "@/components/brand";

export default function OnboardingLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <div className="min-h-screen bg-canvas">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5 sm:px-8">
        <Brand />
        <span className="rounded-full border border-line bg-surface px-4 py-2 text-sm font-semibold text-muted">
          Configuración inicial
        </span>
      </header>
      <main
        className="mx-auto max-w-6xl px-5 pb-16 pt-8 sm:px-8 sm:pt-14"
        id="main-content"
      >
        {children}
      </main>
    </div>
  );
}
