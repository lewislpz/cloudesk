import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatusPanel } from "@/components/ui/status-panel";
import { scanAccessibility } from "@/test/accessibility";

describe("StatusPanel", () => {
  it.each([
    ["loading", "Cargando proyectos", "status"],
    ["empty", "Todavía no hay proyectos", "status"],
    ["error", "No pudimos cargar los proyectos", "alert"],
  ] as const)("announces the %s state", async (tone, title, role) => {
    const { container } = render(
      <StatusPanel
        description="Puedes continuar desde aquí."
        title={title}
        tone={tone}
      />,
    );

    expect(screen.getByRole(role)).toHaveAccessibleName(title);
    expect((await scanAccessibility(container)).violations).toEqual([]);
  });
});
