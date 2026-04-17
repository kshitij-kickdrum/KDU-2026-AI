import Alert from "@mui/material/Alert";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import { formatDateTime } from "@/helpers/dateUtils";
import { useGetHealthQuery } from "@/store/api/adminApi";

export const HealthMonitor = () => {
  const { data } = useGetHealthQuery();

  return (
    <Paper sx={{ p: 2 }}>
      <Stack spacing={1}>
        <Typography variant="h6">System Health</Typography>
        <Alert severity={data?.status === "ok" ? "success" : "warning"}>
          Status: {data?.status ?? "unknown"}
        </Alert>
        <Typography variant="body2">Database: {data?.database ?? "unknown"}</Typography>
        <Typography variant="body2">Config: {data?.config ?? "unknown"}</Typography>
        {data?.timestamp ? <Typography variant="caption">Updated: {formatDateTime(data.timestamp)}</Typography> : null}
      </Stack>
    </Paper>
  );
};
