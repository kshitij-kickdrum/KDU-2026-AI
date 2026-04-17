import Button from "@mui/material/Button";
import MenuItem from "@mui/material/MenuItem";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";

import {
  useActivatePromptMutation,
  useGetPromptsQuery,
} from "@/store/api/adminApi";

const CATEGORIES = ["faq", "complaint", "booking"];

export const PromptManager = () => {
  const { data } = useGetPromptsQuery();
  const [activatePrompt, { isLoading }] = useActivatePromptMutation();

  return (
    <Paper sx={{ p: 2 }}>
      <Stack spacing={2}>
        <Typography variant="h6">Prompt Manager</Typography>
        {CATEGORIES.map((category) => {
          const entry = data?.registry?.[category];
          if (!entry) {
            return null;
          }
          return (
            <Stack key={category} direction={{ xs: "column", md: "row" }} spacing={1} alignItems="center">
              <Typography sx={{ width: 120 }}>{category}</Typography>
              <TextField
                select
                size="small"
                defaultValue={entry.active_version}
                sx={{ minWidth: 180 }}
                onChange={(event) =>
                  activatePrompt({ category, version: event.target.value })
                }
              >
                {entry.available_versions.map((v) => (
                  <MenuItem key={v} value={v}>{v}</MenuItem>
                ))}
              </TextField>
              <Button variant="outlined" disabled={isLoading}>Activate</Button>
            </Stack>
          );
        })}
      </Stack>
    </Paper>
  );
};
