import Stack from "@mui/material/Stack";

import Analytics from "@/components/admin/Analytics";
import ConfigManager from "@/components/admin/ConfigManager";
import CostMonitor from "@/components/admin/CostMonitor";
import Dashboard from "@/components/admin/Dashboard";
import HealthMonitor from "@/components/admin/HealthMonitor";
import PromptManager from "@/components/admin/PromptManager";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import { useGetAdminStatsQuery } from "@/store/api/adminApi";

export const AdminDashboard = () => {
  const { data, isFetching } = useGetAdminStatsQuery(undefined, { pollingInterval: 30000 });

  if (isFetching && !data) {
    return <LoadingSpinner label="Loading dashboard" />;
  }

  return (
    <Stack spacing={2}>
      <Dashboard stats={data} />
      <CostMonitor stats={data} />
      <Analytics stats={data} />
      <PromptManager />
      <ConfigManager />
      <HealthMonitor />
    </Stack>
  );
};
