import Snackbar from "@mui/material/Snackbar";
import Alert from "@mui/material/Alert";

import { useNotifications } from "@/hooks/useNotifications";

export const NotificationSystem = () => {
  const { notifications, dismiss } = useNotifications();
  return (
    <>
      {notifications.map((note) => (
        <Snackbar
          key={note.id}
          open
          autoHideDuration={note.autoHide ? note.duration ?? 4000 : null}
          onClose={() => dismiss(note.id)}
          anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        >
          <Alert onClose={() => dismiss(note.id)} severity={note.type} variant="filled">
            {note.message}
          </Alert>
        </Snackbar>
      ))}
    </>
  );
};
