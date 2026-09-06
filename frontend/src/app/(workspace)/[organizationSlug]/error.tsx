"use client";

import { StatusPanel } from "@/components/ui/status-panel";

export default function WorkspaceError({ reset }: { reset: () => void }) {
  return (
    <StatusPanel
      action={
        <button
          className="inline-flex min-h-11 items-center rounded-full bg-ink px-5 font-semibold text-white hover:bg-brand-strong"
          onClick={reset}
          type="button"
        >
          Volver a intentarlo
        </button>
      }
      description="No se ha perdido ningún cambio. Puedes reintentar la carga de este espacio."
      title="No pudimos cargar el espacio"
      tone="error"
    />
  );
}
