import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import OnboardingLayout from "@/app/(onboarding)/layout";
import OnboardingPage from "@/app/(onboarding)/onboarding/page";
import PublicLayout from "@/app/(public)/layout";
import PublicPage from "@/app/(public)/page";
import WorkspaceLayout from "@/app/(workspace)/[organizationSlug]/layout";
import WorkspacePage from "@/app/(workspace)/[organizationSlug]/page";
import { scanAccessibility } from "@/test/accessibility";

describe("application shells", () => {
  it("renders the public shell with a primary destination", async () => {
    const { container } = render(
      <PublicLayout>
        <PublicPage />
      </PublicLayout>,
    );

    expect(
      screen.getByRole("heading", { level: 1, name: /trabajo facturable/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /configurar espacio/i }),
    ).toHaveAttribute("href", "/onboarding");
    expect((await scanAccessibility(container)).violations).toEqual([]);
  });

  it("renders a guided onboarding shell", async () => {
    const { container } = render(
      <OnboardingLayout>
        <OnboardingPage />
      </OnboardingLayout>,
    );

    expect(
      screen.getByRole("heading", { level: 1, name: /prepara tu espacio/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("list", { name: /progreso/i })).toBeInTheDocument();
    expect((await scanAccessibility(container)).violations).toEqual([]);
  });

  it("renders the tenant workspace around server content", async () => {
    const route = { organizationSlug: "north-star" };
    const page = await WorkspacePage({ params: Promise.resolve(route) });
    const layout = await WorkspaceLayout({
      children: page,
      params: Promise.resolve(route),
    });
    const { container } = render(layout);

    expect(
      screen.getByRole("navigation", { name: /espacio de trabajo/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 1, name: /panel de north star/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/sesión segura del servidor/i)).toBeInTheDocument();
    expect((await scanAccessibility(container)).violations).toEqual([]);
  });
});
