import { useState } from "react";

import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import CachedIcon from "@mui/icons-material/Cached";
import StarBorderIcon from "@mui/icons-material/StarBorder";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import IconButton from "@mui/material/IconButton";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import { formatUsd } from "@/helpers/formatting";
import type { QueryResponse } from "@/types/api";

interface ResponseDisplayProps {
  response?: QueryResponse;
  error?: string;
  isLoading: boolean;
}

export const ResponseDisplay = ({ response, error, isLoading }: ResponseDisplayProps) => {
  const [rating, setRating] = useState<number | null>(null);

  if (isLoading) {
    return <Alert severity="info">Generating your response...</Alert>;
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (!response) {
    return <Alert severity="info">Submit a query to view the AI response and metadata.</Alert>;
  }

  return (
    <Paper sx={{ p: 2 }}>
      <Stack spacing={2}>
        <Typography variant="h6">Response</Typography>
        <Typography whiteSpace="pre-wrap">{response.response}</Typography>
        <Stack direction="row" gap={1} flexWrap="wrap">
          <Chip label={`ID: ${response.query_id}`} />
          <Chip label={`Category: ${response.category}`} />
          <Chip label={`Complexity: ${response.complexity}`} />
          <Chip label={`Model: ${response.model_used}`} />
          <Chip label={`Cost: ${formatUsd(response.cost_usd)}`} />
          <Chip label={`Latency: ${response.latency_ms}ms`} />
          {response.cache_hit ? <Chip icon={<CachedIcon />} color="success" label="Cache hit" /> : null}
          {response.was_summarized ? (
            <Chip icon={<CheckCircleOutlineIcon />} color="warning" label="Summarized" />
          ) : null}
        </Stack>
        <Box>
          <Typography variant="body2" sx={{ mb: 1 }}>
            Rate this response
          </Typography>
          <Stack direction="row">
            {[1, 2, 3, 4, 5].map((n) => (
              <IconButton
                key={n}
                aria-label={`Rate ${n} star`}
                onClick={() => setRating(n)}
                color={rating && n <= rating ? "warning" : "default"}
              >
                <StarBorderIcon />
              </IconButton>
            ))}
          </Stack>
        </Box>
      </Stack>
    </Paper>
  );
};
