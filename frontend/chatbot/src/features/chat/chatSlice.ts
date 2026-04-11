import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { ChatMessage, Style, Toast } from '../../types';

interface ChatState {
  messages: ChatMessage[];
  sessionId: string;
  isLoading: boolean;
  activeStyle: Style;
  toasts: Toast[];
}

const initialState: ChatState = {
  messages: [],
  sessionId: '',
  isLoading: false,
  activeStyle: 'expert',
  toasts: [],
};

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    setSessionId(state, action: PayloadAction<string>) {
      state.sessionId = action.payload;
    },
    setMessages(state, action: PayloadAction<ChatMessage[]>) {
      state.messages = action.payload;
    },
    setActiveStyle(state, action: PayloadAction<Style>) {
      state.activeStyle = action.payload;
    },
    addMessage(state, action: PayloadAction<ChatMessage>) {
      state.messages.push(action.payload);
    },
    setLoading(state, action: PayloadAction<boolean>) {
      state.isLoading = action.payload;
    },
    clearMessages(state) {
      state.messages = [];
    },
    addToast(state, action: PayloadAction<Toast>) {
      state.toasts.push(action.payload);
    },
    removeToast(state, action: PayloadAction<string>) {
      state.toasts = state.toasts.filter((t) => t.id !== action.payload);
    },
  },
});

export const {
  setSessionId,
  setMessages,
  setActiveStyle,
  addMessage,
  setLoading,
  clearMessages,
  addToast,
  removeToast,
} = chatSlice.actions;

export default chatSlice.reducer;
