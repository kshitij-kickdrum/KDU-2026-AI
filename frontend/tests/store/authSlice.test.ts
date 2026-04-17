import { describe, expect, it } from "vitest";

import authReducer, { loginFailure, loginSuccess, logout } from "@/store/slices/authSlice";

describe("authSlice", () => {
  it("handles login success", () => {
    const state = authReducer(undefined, loginSuccess({ token: "x", user: { username: "a", role: "admin" } }));
    expect(state.isAuthenticated).toBe(true);
  });

  it("locks after failed attempts", () => {
    let state = authReducer(undefined, loginFailure());
    state = authReducer(state, loginFailure());
    state = authReducer(state, loginFailure());
    state = authReducer(state, loginFailure());
    state = authReducer(state, loginFailure());
    expect(state.lockedUntil).toBeDefined();
  });

  it("logs out", () => {
    const loggedIn = authReducer(undefined, loginSuccess({ token: "x", user: { username: "a", role: "admin" } }));
    const state = authReducer(loggedIn, logout());
    expect(state.isAuthenticated).toBe(false);
  });
});
