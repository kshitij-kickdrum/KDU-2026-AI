import Button from "@mui/material/Button";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import { useReloadConfigMutation } from "@/store/api/adminApi";

export const ConfigManager = () => {
  const [reloadConfig, { data, isLoading }] = useReloadConfigMutation();
  return (
    <Paper sx={{ p: 2 }}>
      <Stack spacing={2}>
        <Typography variant="h6">Configuration</Typography>
        <Button variant="contained" onClick={() => reloadConfig()} disabled={isLoading}>
          Reload Config
        </Button>
        {data ? (
          <Typography variant="body2">
            {data.message}: {data.reloaded_files.join(", ")}
          </Typography>
        ) : null}
      </Stack>
    </Paper>
  );
};
