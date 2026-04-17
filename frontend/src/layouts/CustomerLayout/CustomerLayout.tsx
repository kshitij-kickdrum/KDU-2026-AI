import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Container from "@mui/material/Container";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";

import { APP_TITLE } from "@/config/constants";

interface CustomerLayoutProps {
  children: ReactNode;
}

export const CustomerLayout = ({ children }: CustomerLayoutProps) => (
  <Box>
    <AppBar position="sticky" color="transparent" elevation={0}>
      <Toolbar>
        <Typography variant="h6">{APP_TITLE}</Typography>
      </Toolbar>
    </AppBar>
    <Container id="main-content" maxWidth="lg" sx={{ py: 3 }}>
      {children}
    </Container>
  </Box>
);
import type { ReactNode } from "react";
