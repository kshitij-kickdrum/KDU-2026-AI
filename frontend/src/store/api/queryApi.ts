import { createApi, fetchBaseQuery, retry } from "@reduxjs/toolkit/query/react";

import { apiConfig } from "@/config/api";
import type { QueryResponse, QuerySubmission } from "@/types/api";

const baseQuery = fetchBaseQuery({
  baseUrl: apiConfig.baseUrl,
  prepareHeaders: (headers) => {
    headers.set("Content-Type", "application/json");
    return headers;
  },
});

const baseQueryWithRetry = retry(baseQuery, { maxRetries: 3 });

export const queryApi = createApi({
  reducerPath: "queryApi",
  baseQuery: baseQueryWithRetry,
  tagTypes: ["Query"],
  endpoints: (builder) => ({
    submitQuery: builder.mutation<QueryResponse, QuerySubmission>({
      query: (queryData) => ({
        url: "/query",
        method: "POST",
        body: queryData,
      }),
      invalidatesTags: ["Query"],
    }),
  }),
});

export const { useSubmitQueryMutation } = queryApi;
