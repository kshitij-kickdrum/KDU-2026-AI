import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

import { SESSION_TIMEOUT_MS } from "@/config/constants";
import type { AuthState, UserInfo } from "@/types/auth";

const initialState: AuthState = {
  isAuthenticated: false,
  failedAttempts: 0,
};

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    loginSuccess: (state, action: PayloadAction<{ token: string; user: UserInfo }>) => {
      state.isAuthenticated = true;
      state.token = action.payload.token;
      state.user = action.payload.user;
      state.failedAttempts = 0;
      state.lockedUntil = undefined;
      state.sessionExpiry = Date.now() + SESSION_TIMEOUT_MS;
    },
    loginFailure: (state) => {
      state.failedAttempts += 1;
      if (state.failedAttempts >= 5) {
        state.lockedUntil = Date.now() + 15 * 60 * 1000;
      }
    },
    refreshSession: (state, action: PayloadAction<number>) => {
      state.sessionExpiry = action.payload;
    },
    logout: (state) => {
      state.isAuthenticated = false;
      state.token = undefined;
      state.user = undefined;
      state.sessionExpiry = undefined;
    },
  },
});

export const { loginSuccess, loginFailure, refreshSession, logout } = authSlice.actions;
export default authSlice.reducer;
