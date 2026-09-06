"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { createContext, type ReactNode, useContext, useState } from "react";

import type { Client } from "@/lib/api/generated/client";
import { createQueryClient } from "@/lib/query/create-query-client";

import { createBrowserApiClient } from "./browser-client";

const ApiClientContext = createContext<Client | null>(null);

type RuntimeProviderProps = Readonly<{
  apiBaseUrl?: string;
  children: ReactNode;
  csrfToken?: string;
}>;

export function RuntimeProvider({
  apiBaseUrl = "/",
  children,
  csrfToken,
}: RuntimeProviderProps) {
  const [apiClient] = useState(() =>
    createBrowserApiClient({ baseUrl: apiBaseUrl, csrfToken }),
  );
  const [queryClient] = useState(createQueryClient);

  return (
    <ApiClientContext.Provider value={apiClient}>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </ApiClientContext.Provider>
  );
}

export function useApiClient(): Client {
  const apiClient = useContext(ApiClientContext);
  if (!apiClient) {
    throw new Error("useApiClient must be used inside RuntimeProvider.");
  }
  return apiClient;
}
