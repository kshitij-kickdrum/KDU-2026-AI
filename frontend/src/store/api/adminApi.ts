import { createApi, fetchBaseQuery, retry } from "@reduxjs/toolkit/query/react";

import { apiConfig } from "@/config/api";
import type {
  ActivatePromptRequest,
  ActivatePromptResponse,
  AdminStats,
  ConfigReloadResponse,
  HealthResponse,
  PromptRegistry,
} from "@/types/api";

const baseQuery = fetchBaseQuery({
  baseUrl: apiConfig.baseUrl,
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as { auth: { token?: string } }).auth.token;
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    return headers;
  },
});

const baseQueryWithRetry = retry(baseQuery, { maxRetries: 3 });

export const adminApi = createApi({
  reducerPath: "adminApi",
  baseQuery: baseQueryWithRetry,
  tagTypes: ["AdminStats", "Prompts", "Config", "Health"],
  endpoints: (builder) => ({
    getAdminStats: builder.query<AdminStats, void>({
      query: () => "/admin/stats",
      providesTags: ["AdminStats"],
      keepUnusedDataFor: 30,
    }),
    getPrompts: builder.query<PromptRegistry, void>({
      query: () => "/admin/prompts",
      providesTags: ["Prompts"],
    }),
    activatePrompt: builder.mutation<ActivatePromptResponse, ActivatePromptRequest>({
      query: (data) => ({
        url: "/admin/prompts/activate",
        method: "POST",
        body: data,
      }),
      invalidatesTags: ["Prompts", "AdminStats"],
    }),
    reloadConfig: builder.mutation<ConfigReloadResponse, void>({
      query: () => ({
        url: "/admin/config/reload",
        method: "POST",
      }),
      invalidatesTags: ["Config", "AdminStats"],
    }),
    getHealth: builder.query<HealthResponse, void>({
      query: () => "/health",
      providesTags: ["Health"],
    }),
  }),
});

export const {
  useGetAdminStatsQuery,
  useGetPromptsQuery,
  useActivatePromptMutation,
  useReloadConfigMutation,
  useGetHealthQuery,
} = adminApi;
