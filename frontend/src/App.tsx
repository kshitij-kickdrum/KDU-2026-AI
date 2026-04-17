import { lazy, Suspense, useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";

import AccessibilityProvider from "@/components/common/AccessibilityProvider";
import { ErrorBoundary } from "@/components/common/ErrorBoundary/ErrorBoundary";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import NotificationSystem from "@/components/common/NotificationSystem";

const CustomerPage = lazy(() => import("@/pages/CustomerPage"));
const AdminPage = lazy(() => import("@/pages/AdminPage"));
const LoginPage = lazy(() => import("@/pages/LoginPage"));
const NotFoundPage = lazy(() => import("@/pages/NotFoundPage"));

const App = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const setOnline = () => setIsOnline(true);
    const setOffline = () => setIsOnline(false);
    const rejectHandler = () => {
      console.error("Unhandled promise rejection captured by global handler");
    };
    window.addEventListener("online", setOnline);
    window.addEventListener("offline", setOffline);
    window.addEventListener("unhandledrejection", rejectHandler);
    return () => {
      window.removeEventListener("online", setOnline);
      window.removeEventListener("offline", setOffline);
      window.removeEventListener("unhandledrejection", rejectHandler);
    };
  }, []);

  return (
    <AccessibilityProvider>
      <ErrorBoundary>
        <Box>
          {!isOnline ? <Alert severity="warning">You are offline. Some features are unavailable.</Alert> : null}
          <Suspense fallback={<LoadingSpinner label="Loading app" />}>
            <Routes>
              <Route path="/" element={<CustomerPage />} />
              <Route path="/admin" element={<AdminPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/404" element={<NotFoundPage />} />
              <Route path="*" element={<Navigate to="/404" replace />} />
            </Routes>
          </Suspense>
          <NotificationSystem />
        </Box>
      </ErrorBoundary>
    </AccessibilityProvider>
  );
};

export default App;
