import { describe, expect, it } from "vitest";

import { createBrowserApiClient } from "@/lib/api/runtime/browser-client";

function jsonResponse(): Response {
  return new Response(JSON.stringify({ status: "ok" }), {
    headers: { "Content-Type": "application/json" },
    status: 200,
  });
}

function recordingFetch() {
  const requests: Request[] = [];
  const fetchImplementation = (async (input: RequestInfo | URL) => {
    if (!(input instanceof Request)) {
      throw new TypeError("The generated client must pass a Request instance.");
    }
    requests.push(input);
    return jsonResponse();
  }) as typeof fetch;

  return { fetchImplementation, requests };
}

describe("browser API runtime", () => {
  it("uses same-origin cookies without adding a bearer token", async () => {
    const { fetchImplementation, requests } = recordingFetch();
    const client = createBrowserApiClient({ fetch: fetchImplementation });

    await client.get({ url: "/health/live" });

    const request = requests[0];
    expect(request).toBeInstanceOf(Request);
    expect(request?.credentials).toBe("same-origin");
    expect(request?.headers.has("Authorization")).toBe(false);
  });

  it("adds an injected CSRF token only to unsafe methods", async () => {
    const { fetchImplementation, requests } = recordingFetch();
    const client = createBrowserApiClient({
      csrfToken: "ephemeral-csrf-token",
      fetch: fetchImplementation,
    });

    await client.get({ url: "/health/live" });
    await client.post({ url: "/api/v1/example" });

    const getRequest = requests[0];
    const postRequest = requests[1];
    expect(getRequest?.headers.has("X-CSRF-Token")).toBe(false);
    expect(postRequest?.headers.get("X-CSRF-Token")).toBe(
      "ephemeral-csrf-token",
    );
  });

  it.each(["https://api.example.test", "//api.example.test"])(
    "rejects credentialed cross-origin base URL %s",
    (baseUrl) => {
      expect(() => createBrowserApiClient({ baseUrl })).toThrow(
        /same-origin path/i,
      );
    },
  );
});
