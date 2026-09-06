"use client";

import { StatusPanel } from "@/components/ui/status-panel";

export default function ApplicationError({ reset }: { reset: () => void }) {
  return (
    <main className="mx-auto max-w-3xl px-5 py-20" id="main-content">
      <StatusPanel
        action={
          <button
            className="inline-flex min-h-11 items-center rounded-full bg-ink px-5 font-semibold text-white"
            onClick={reset}
            type="button"
          >
            Reintentar
          </button>
        }
        description="Ha ocurrido un problema inesperado al preparar esta vista."
        title="Algo no ha salido bien"
        tone="error"
      />
    </main>
  );
}
