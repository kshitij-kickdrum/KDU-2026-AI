export interface Notification {
  id: string;
  type: "success" | "error" | "warning" | "info";
  message: string;
  autoHide?: boolean;
  duration?: number;
}

export interface UIState {
  theme: "light" | "dark";
  globalLoading: boolean;
  globalError?: string;
  sidebarOpen: boolean;
}

export interface FAQQuestion {
  id: string;
  question: string;
  answer: string;
  category: string;
  popularity: number;
}
