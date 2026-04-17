import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import Box from "@mui/material/Box";
import Container from "@mui/material/Container";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import { useAppSelector } from "@/store";

interface AdminLayoutProps {
  children: ReactNode;
}

export const AdminLayout = ({ children }: AdminLayoutProps) => {
  const auth = useAppSelector((state) => state.auth);
  if (!auth.isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <Container maxWidth="lg" sx={{ py: 3 }} id="main-content">
      <Stack spacing={2}>
        <Typography variant="h4">Admin Dashboard</Typography>
        <Box>{children}</Box>
      </Stack>
    </Container>
  );
};
