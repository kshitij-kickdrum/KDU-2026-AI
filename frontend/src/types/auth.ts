export interface UserInfo {
  username: string;
  role: "admin" | "customer";
}

export interface AuthState {
  isAuthenticated: boolean;
  token?: string;
  user?: UserInfo;
  failedAttempts: number;
  lockedUntil?: number;
  sessionExpiry?: number;
}
