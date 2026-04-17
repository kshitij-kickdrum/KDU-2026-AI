import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { SESSION_TIMEOUT_MS } from "@/config/constants";
import { useAppDispatch, useAppSelector } from "@/store";
import { logout, refreshSession } from "@/store/slices/authSlice";

export const useAuth = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const auth = useAppSelector((state) => state.auth);

  useEffect(() => {
    if (!auth.isAuthenticated || !auth.sessionExpiry) {
      return;
    }
    const remaining = auth.sessionExpiry - Date.now();
    if (remaining <= 0) {
      dispatch(logout());
      navigate("/login");
      return;
    }
    const timer = window.setTimeout(() => {
      dispatch(logout());
      navigate("/login");
    }, remaining);
    return () => window.clearTimeout(timer);
  }, [auth.isAuthenticated, auth.sessionExpiry, dispatch, navigate]);

  const touch = () => dispatch(refreshSession(Date.now() + SESSION_TIMEOUT_MS));

  return { auth, touch };
};
