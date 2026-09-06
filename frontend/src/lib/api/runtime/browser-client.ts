import { createClient, type Client } from "@/lib/api/generated/client";

export type BrowserApiClientOptions = Readonly<{
  baseUrl?: string;
  csrfToken?: string;
  fetch?: typeof fetch;
}>;

const safeMethods = new Set(["GET", "HEAD", "OPTIONS"]);

function assertSameOriginPath(baseUrl: string): void {
  if (!baseUrl.startsWith("/") || baseUrl.startsWith("//")) {
    throw new Error("The browser API base URL must be a same-origin path.");
  }
}

function resolveBaseUrl(baseUrl: string): string {
  const origin =
    typeof globalThis.location === "undefined"
      ? "http://localhost"
      : globalThis.location.origin;
  return new URL(baseUrl, `${origin}/`).toString();
}

export function createBrowserApiClient({
  baseUrl = "/",
  csrfToken,
  fetch: fetchImplementation,
}: BrowserApiClientOptions = {}): Client {
  assertSameOriginPath(baseUrl);

  const apiClient = createClient({
    baseUrl: resolveBaseUrl(baseUrl),
    credentials: "same-origin",
    fetch: fetchImplementation,
    throwOnError: true,
  });
  const normalizedCsrfToken = csrfToken?.trim();

  if (normalizedCsrfToken) {
    apiClient.interceptors.request.use((request) => {
      if (!safeMethods.has(request.method.toUpperCase())) {
        request.headers.set("X-CSRF-Token", normalizedCsrfToken);
      }
      return request;
    });
  }

  return apiClient;
}
