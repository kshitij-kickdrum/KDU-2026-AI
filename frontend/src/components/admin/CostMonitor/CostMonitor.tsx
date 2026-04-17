import Button from "@mui/material/Button";
import LinearProgress from "@mui/material/LinearProgress";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import { formatUsd } from "@/helpers/formatting";
import type { AdminStats } from "@/types/api";

interface CostMonitorProps {
  stats?: AdminStats;
}

const toCsv = (stats: AdminStats): string => {
  return [
    "period,total_queries,total_cost_usd",
    `daily,${stats.daily_stats.total_queries},${stats.daily_stats.total_cost_usd}`,
    `monthly,${stats.monthly_stats.total_queries},${stats.monthly_stats.total_cost_usd}`,
  ].join("\n");
};

export const CostMonitor = ({ stats }: CostMonitorProps) => {
  if (!stats) {
    return <Typography>No cost data.</Typography>;
  }

  const dailyBudget = 1;
  const monthlyBudget = 20;
  const dailyProgress = Math.min((stats.daily_stats.total_cost_usd / dailyBudget) * 100, 100);
  const monthlyProgress = Math.min((stats.monthly_stats.total_cost_usd / monthlyBudget) * 100, 100);

  const exportCsv = () => {
    const blob = new Blob([toCsv(stats)], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "fixit-cost-report.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Paper sx={{ p: 2 }}>
      <Stack spacing={2}>
        <Typography variant="h6">Cost Monitor</Typography>
        <Typography>Daily: {formatUsd(stats.daily_stats.total_cost_usd)} / {formatUsd(dailyBudget)}</Typography>
        <LinearProgress variant="determinate" value={dailyProgress} color={dailyProgress >= 80 ? "warning" : "primary"} />
        <Typography>Monthly: {formatUsd(stats.monthly_stats.total_cost_usd)} / {formatUsd(monthlyBudget)}</Typography>
        <LinearProgress variant="determinate" value={monthlyProgress} color={monthlyProgress >= 80 ? "warning" : "primary"} />
        <Button variant="outlined" onClick={exportCsv}>Export CSV</Button>
      </Stack>
    </Paper>
  );
};
