import { configureStore } from '@reduxjs/toolkit'

import { tradingApi } from '../api/api'
import { uiReducer } from './slices/uiSlice'

export const store = configureStore({
  reducer: {
    ui: uiReducer,
    [tradingApi.reducerPath]: tradingApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(tradingApi.middleware),
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
