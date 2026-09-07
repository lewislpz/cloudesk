import { describe, expect, it } from "vitest";

import { getOrganization, getReadiness } from "@/lib/api/generated/sdk.gen";
import { createBrowserApiClient } from "@/lib/api/runtime/browser-client";

describe("generated transport contract", () => {
  it("keeps organization identifiers in the generated tenant path", async () => {
    const organizationId = "2e4cf420-792d-4c89-a768-0d68e9235a7e";
    let requestedUrl = "";
    const client = createBrowserApiClient({
      fetch: (async (input: Request) => {
        requestedUrl = input.url;
        return Response.json({ id: organizationId, name: "Fixture" });
      }) as typeof fetch,
    });

    await getOrganization({ client, path: { organizationId } });

    expect(new URL(requestedUrl).pathname).toBe(
      `/api/v1/organizations/${organizationId}`,
    );
  });

  it("preserves correlated API error envelopes", async () => {
    const error = {
      code: "SERVICE_UNAVAILABLE",
      message: "The service is temporarily unavailable.",
      requestId: "contract-503",
    };
    const client = createBrowserApiClient({
      fetch: (async () =>
        Response.json({ error }, { status: 503 })) as typeof fetch,
    });

    await expect(getReadiness({ client })).rejects.toEqual({ error });
  });

  it("propagates cancellation to the fetch boundary", async () => {
    const controller = new AbortController();
    controller.abort();
    const client = createBrowserApiClient({
      fetch: (async (input: Request) => {
        expect(input.signal.aborted).toBe(true);
        input.signal.throwIfAborted();
        throw new Error("aborted request reached transport");
      }) as typeof fetch,
    });

    await expect(
      getReadiness({ client, signal: controller.signal }),
    ).rejects.toMatchObject({ name: "AbortError" });
  });
});
