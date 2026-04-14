import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

import type {
  ApproveRequest,
  ApproveResponse,
  HealthResponse,
  RunRequest,
  RunResponse,
  SessionStateResponse,
  SessionsResponse,
  StateResponse,
  SymbolSearchResult,
} from './types'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || 'http://localhost:8000/api/v1'

export const tradingApi = createApi({
  reducerPath: 'tradingApi',
  baseQuery: fetchBaseQuery({
    baseUrl: API_BASE_URL,
    prepareHeaders: (headers) => {
      headers.set('Content-Type', 'application/json')
      return headers
    },
  }),
  tagTypes: ['Health', 'ThreadState'],
  endpoints: (builder) => ({
    getHealth: builder.query<HealthResponse, void>({
      query: () => '/health',
      providesTags: ['Health'],
    }),
    searchSymbols: builder.query<{ result: SymbolSearchResult[] }, string>({
      query: (q) => `/symbols/search?q=${encodeURIComponent(q)}`,
    }),
    runAgent: builder.mutation<RunResponse, RunRequest>({
      query: (body) => ({
        url: '/run',
        method: 'POST',
        body,
      }),
      invalidatesTags: (_result, _error, arg) => [
        { type: 'ThreadState', id: arg.thread_id },
      ],
    }),
    approveTrade: builder.mutation<ApproveResponse, ApproveRequest>({
      query: (body) => ({
        url: '/approve',
        method: 'POST',
        body,
      }),
      invalidatesTags: (_result, _error, arg) => [
        { type: 'ThreadState', id: arg.thread_id },
      ],
    }),
    getThreadState: builder.query<StateResponse, string>({
      query: (threadId) => `/state/${encodeURIComponent(threadId)}`,
      providesTags: (_result, _error, threadId) => [
        { type: 'ThreadState', id: threadId },
      ],
    }),
    getSessions: builder.query<SessionsResponse, number | void>({
      query: (limit = 20) => `/sessions?limit=${limit}`,
    }),
    getSessionState: builder.query<SessionStateResponse, string>({
      query: (sessionRef) => `/sessions/${encodeURIComponent(sessionRef)}`,
    }),
  }),
})

export const {
  useGetHealthQuery,
  useLazySearchSymbolsQuery,
  useRunAgentMutation,
  useApproveTradeMutation,
  useGetThreadStateQuery,
  useGetSessionsQuery,
  useLazyGetSessionStateQuery,
  useLazyGetThreadStateQuery,
} = tradingApi
