import axe, { type AxeResults } from "axe-core";

export async function scanAccessibility(
  container: Element,
): Promise<AxeResults> {
  return axe.run(container, {
    rules: {
      // jsdom has no layout engine, so contrast remains a browser-level gate.
      "color-contrast": { enabled: false },
    },
  });
}
