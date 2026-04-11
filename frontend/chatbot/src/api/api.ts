import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type {
  RegisterRequest,
  RegisterResponse,
  ChatRequest,
  ChatApiResponse,
  ImageApiResponse,
  HistoryResponse,
  SessionSummary,
  DeleteSessionRequest,
  SessionListResponse,
  UserProfile,
} from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({ baseUrl: BASE_URL }),
  tagTypes: ['History', 'Session'],
  endpoints: (builder) => ({

    // POST /user/register
    registerUser: builder.mutation<RegisterResponse, RegisterRequest>({
      query: (body) => ({
        url: '/user/register',
        method: 'POST',
        body,
      }),
    }),

    // GET /user/{user_id}
    getUser: builder.query<UserProfile, string>({
      query: (userId) => `/user/${userId}`,
    }),

    // POST /chat
    sendChat: builder.mutation<ChatApiResponse, ChatRequest>({
      query: (body) => ({
        url: '/chat',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['History', 'Session'],
    }),

    // POST /image  (FormData — handled manually in the hook, this is typed for reference)
    sendImage: builder.mutation<ImageApiResponse, FormData>({
      query: (formData) => ({
        url: '/image',
        method: 'POST',
        body: formData,
      }),
      invalidatesTags: ['History', 'Session'],
    }),

    getSessions: builder.query<SessionListResponse, string>({
      query: (userId) => `/sessions?user_id=${userId}`,
      providesTags: ['Session'],
    }),

    createSession: builder.mutation<{ message: string }, { user_id: string; session_id: string }>({
      query: (body) => ({
        url: '/session',
        method: 'POST',
        body,
      }),
      async onQueryStarted({ user_id, session_id }, { dispatch, queryFulfilled }) {
        const placeholder: SessionSummary = {
          session_id,
          title: 'New chat',
          preview: '',
          created_at: Date.now(),
          updated_at: Date.now(),
          message_count: 0,
        };

        const patch = dispatch(
          api.util.updateQueryData('getSessions', user_id, (draft) => {
            if (!draft.sessions.some((item) => item.session_id === session_id)) {
              draft.sessions.unshift(placeholder);
            }
          }),
        );

        try {
          await queryFulfilled;
        } catch {
          patch.undo();
        }
      },
      invalidatesTags: ['Session'],
    }),

    // GET /history?session_id=&user_id=
    getHistory: builder.query<HistoryResponse, { session_id: string; user_id: string }>({
      query: ({ session_id, user_id }) =>
        `/history?session_id=${session_id}&user_id=${user_id}`,
      providesTags: ['History'],
    }),

    // DELETE /session
    deleteSession: builder.mutation<void, DeleteSessionRequest>({
      query: (body) => ({
        url: '/session',
        method: 'DELETE',
        body,
      }),
      invalidatesTags: ['History', 'Session'],
    }),

  }),
});

export const {
  useRegisterUserMutation,
  useGetUserQuery,
  useSendChatMutation,
  useSendImageMutation,
  useGetSessionsQuery,
  useCreateSessionMutation,
  useGetHistoryQuery,
  useDeleteSessionMutation,
} = api;
