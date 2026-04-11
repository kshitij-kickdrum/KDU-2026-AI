import { configureStore } from '@reduxjs/toolkit';
import { api } from '../api/api';
import authReducer from '../features/auth/authSlice';
import chatReducer from '../features/chat/chatSlice';
import imageReducer from '../features/imageAnalysis/imageSlice';

export const store = configureStore({
  reducer: {
    [api.reducerPath]: api.reducer,
    auth: authReducer,
    chat: chatReducer,
    image: imageReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(api.middleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
