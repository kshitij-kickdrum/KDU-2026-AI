import type { ReactNode } from "react";

import Container from "@mui/material/Container";

interface AuthLayoutProps {
  children: ReactNode;
}

export const AuthLayout = ({ children }: AuthLayoutProps) => (
  <Container maxWidth="sm">{children}</Container>
);
