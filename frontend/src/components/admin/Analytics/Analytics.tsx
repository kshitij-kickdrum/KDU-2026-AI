import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { AdminStats } from "@/types/api";

interface AnalyticsProps {
  stats?: AdminStats;
}

export const Analytics = ({ stats }: AnalyticsProps) => {
  const byCategory = stats?.daily_stats.by_category ?? {};
  return (
    <Paper sx={{ p: 2 }}>
      <Stack spacing={1}>
        <Typography variant="h6">Analytics</Typography>
        {Object.entries(byCategory).map(([name, value]) => (
          <Typography key={name}>
            {name}: {value.queries} queries, ${value.cost_usd.toFixed(2)}
          </Typography>
        ))}
      </Stack>
    </Paper>
  );
};
