import Link from "next/link";

import { StatusPanel } from "@/components/ui/status-panel";

export default function NotFound() {
  return (
    <main className="mx-auto max-w-3xl px-5 py-20" id="main-content">
      <StatusPanel
        action={
          <Link
            className="inline-flex min-h-11 items-center rounded-full bg-ink px-5 font-semibold text-white"
            href="/"
          >
            Volver al inicio
          </Link>
        }
        description="La dirección no corresponde a una vista disponible."
        title="No encontramos esta página"
        tone="empty"
      />
    </main>
  );
}
