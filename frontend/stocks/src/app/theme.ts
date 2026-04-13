import { createTheme } from '@mui/material'

export const appTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#47d6ff',
      light: '#b6ebff',
      dark: '#00677f',
    },
    secondary: {
      main: '#00fd9b',
    },
    error: {
      main: '#ffb4ab',
    },
    background: {
      default: '#0f131c',
      paper: '#1c1f29',
    },
    text: {
      primary: '#dfe2ef',
      secondary: '#bbc9cf',
    },
    divider: 'rgba(60,73,78,0.3)',
  },
  shape: {
    borderRadius: 2,
  },
  typography: {
    fontFamily: '"Inter", "Segoe UI", sans-serif',
    h1: { fontWeight: 800, letterSpacing: '-0.04em' },
    h2: { fontWeight: 800, letterSpacing: '-0.03em' },
    h4: { fontWeight: 800, letterSpacing: '-0.03em' },
    h6: { fontWeight: 700 },
    subtitle2: {
      fontFamily: '"Space Grotesk", sans-serif',
      fontSize: '0.625rem',
      fontWeight: 700,
      letterSpacing: '0.15em',
      textTransform: 'uppercase',
    },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#0f131c',
          color: '#dfe2ef',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: 'rgba(49,53,63,0.4)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(60,73,78,0.15)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 700,
          borderRadius: 8,
        },
        containedPrimary: {
          background: 'linear-gradient(135deg, #00d2ff, #00f1fd)',
          color: '#003543',
          '&:hover': {
            background: 'linear-gradient(135deg, #47d6ff, #00f1fd)',
            boxShadow: '0 0 30px rgba(0,210,255,0.4)',
          },
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          backgroundColor: '#31353f',
          borderRadius: 2,
          '& fieldset': { border: 'none' },
          '&:hover fieldset': { border: 'none' },
          '&.Mui-focused fieldset': {
            border: '1px solid #47d6ff',
          },
        },
        input: {
          fontFamily: '"Space Grotesk", sans-serif',
          color: '#dfe2ef',
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        root: {
          backgroundColor: '#31353f',
          borderRadius: 2,
        },
      },
    },
    MuiInputLabel: {
      styleOverrides: {
        root: {
          fontFamily: '"Space Grotesk", sans-serif',
          fontSize: '0.625rem',
          fontWeight: 700,
          letterSpacing: '0.15em',
          textTransform: 'uppercase',
          color: '#47d6ff',
        },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: {
          fontFamily: '"Space Grotesk", sans-serif',
          backgroundColor: '#1c1f29',
          '&:hover': { backgroundColor: '#262a34' },
          '&.Mui-selected': { backgroundColor: '#262a34' },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { borderRadius: 4 },
      },
    },
  },
})
