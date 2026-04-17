import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { Link } from "react-router-dom";

export const NotFoundPage = () => (
  <Stack spacing={2} alignItems="center" justifyContent="center" minHeight="60vh">
    <Typography variant="h3">404</Typography>
    <Typography>Page not found.</Typography>
    <Button component={Link} to="/" variant="contained">
      Back to Home
    </Button>
  </Stack>
);
