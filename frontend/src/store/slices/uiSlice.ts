import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

import type { UIState } from "@/types/ui";

const initialState: UIState = {
  theme: "light",
  globalLoading: false,
  sidebarOpen: true,
};

const uiSlice = createSlice({
  name: "ui",
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<"light" | "dark">) => {
      state.theme = action.payload;
    },
    setGlobalLoading: (state, action: PayloadAction<boolean>) => {
      state.globalLoading = action.payload;
    },
    setGlobalError: (state, action: PayloadAction<string | undefined>) => {
      state.globalError = action.payload;
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload;
    },
  },
});

export const { setTheme, setGlobalLoading, setGlobalError, setSidebarOpen } = uiSlice.actions;
export default uiSlice.reducer;
