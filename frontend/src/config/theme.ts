import { createTheme } from "@mui/material/styles";

export const appTheme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#0c4a6e",
    },
    secondary: {
      main: "#b45309",
    },
    background: {
      default: "#f8fafc",
      paper: "#ffffff",
    },
  },
  typography: {
    fontFamily: "'DM Sans', 'Segoe UI', sans-serif",
    h1: { fontWeight: 700 },
    h2: { fontWeight: 700 },
    h3: { fontWeight: 600 },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: "none",
          borderRadius: 10,
          minHeight: 44,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          minWidth: 240,
        },
      },
    },
  },
});
