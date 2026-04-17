import { createSlice, nanoid, type PayloadAction } from "@reduxjs/toolkit";

import type { Notification } from "@/types/ui";

interface NotificationState {
  notifications: Notification[];
  maxNotifications: number;
}

const initialState: NotificationState = {
  notifications: [],
  maxNotifications: 5,
};

const notificationSlice = createSlice({
  name: "notifications",
  initialState,
  reducers: {
    addNotification: (
      state,
      action: PayloadAction<Omit<Notification, "id">>,
    ) => {
      state.notifications.push({
        id: nanoid(),
        autoHide: true,
        duration: 4000,
        ...action.payload,
      });
      if (state.notifications.length > state.maxNotifications) {
        state.notifications.shift();
      }
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter((n) => n.id !== action.payload);
    },
    clearNotifications: (state) => {
      state.notifications = [];
    },
  },
});

export const { addNotification, removeNotification, clearNotifications } = notificationSlice.actions;
export default notificationSlice.reducer;
