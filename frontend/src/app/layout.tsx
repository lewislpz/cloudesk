import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  description:
    "Un espacio claro para convertir trabajo de clientes en entregas e ingresos.",
  title: {
    default: "ClouDesk",
    template: "%s · ClouDesk",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="es">
      <body>
        <a
          className="sr-only z-50 rounded-md bg-ink px-4 py-3 text-sm font-semibold text-white focus:not-sr-only focus:fixed focus:left-4 focus:top-4"
          href="#main-content"
        >
          Saltar al contenido principal
        </a>
        {children}
      </body>
    </html>
  );
}
