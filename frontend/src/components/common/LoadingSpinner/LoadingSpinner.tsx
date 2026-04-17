import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

interface LoadingSpinnerProps {
  label?: string;
}

export const LoadingSpinner = ({ label = "Loading" }: LoadingSpinnerProps) => (
  <Stack role="status" aria-live="polite" spacing={1} alignItems="center" py={3}>
    <CircularProgress size={32} />
    <Typography variant="body2">{label}</Typography>
  </Stack>
);
