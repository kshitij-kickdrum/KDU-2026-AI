import Grid from "@mui/material/Grid";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";

import { formatPercent, formatUsd } from "@/helpers/formatting";
import type { AdminStats } from "@/types/api";

interface DashboardProps {
  stats?: AdminStats;
}

export const Dashboard = ({ stats }: DashboardProps) => {
  if (!stats) {
    return <Typography>Dashboard data unavailable.</Typography>;
  }

  const daily = stats.daily_stats;
  const monthly = stats.monthly_stats;

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={4}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="overline">Daily Queries</Typography>
          <Typography variant="h4">{daily.total_queries}</Typography>
        </Paper>
      </Grid>
      <Grid item xs={12} md={4}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="overline">Daily Cost</Typography>
          <Typography variant="h4">{formatUsd(daily.total_cost_usd)}</Typography>
        </Paper>
      </Grid>
      <Grid item xs={12} md={4}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="overline">Cache Hit Rate</Typography>
          <Typography variant="h4">{formatPercent(stats.cache_stats.hit_rate)}</Typography>
        </Paper>
      </Grid>
      <Grid item xs={12}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle1">Monthly total: {formatUsd(monthly.total_cost_usd)}</Typography>
        </Paper>
      </Grid>
    </Grid>
  );
};
