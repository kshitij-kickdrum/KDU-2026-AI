import { useMemo } from "react";

import { useAppDispatch, useAppSelector } from "@/store";
import { addNotification, removeNotification } from "@/store/slices/notificationSlice";

export const useNotifications = () => {
  const dispatch = useAppDispatch();
  const notifications = useAppSelector((state) => state.notifications.notifications);

  return useMemo(
    () => ({
      notifications,
      push: (message: string, type: "success" | "error" | "warning" | "info" = "info") =>
        dispatch(addNotification({ message, type })),
      dismiss: (id: string) => dispatch(removeNotification(id)),
    }),
    [dispatch, notifications],
  );
};
