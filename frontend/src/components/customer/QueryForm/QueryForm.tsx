import { useMemo, useState } from "react";

import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";

import { QUERY_MAX_LENGTH } from "@/config/constants";
import { useDebounce } from "@/hooks/useDebounce";
import { validateQuery } from "@/helpers/validation";
import type { QuerySubmission } from "@/types/api";

interface QueryFormProps {
  isLoading: boolean;
  onSubmit: (payload: QuerySubmission) => void;
}

const EXAMPLES = [
  "My sink has been leaking since this morning. What should I do first?",
  "I need to reschedule my cleaning appointment for Friday afternoon.",
  "I am unhappy with today service and want to file a complaint.",
];

export const QueryForm = ({ isLoading, onSubmit }: QueryFormProps) => {
  const [query, setQuery] = useState("");
  const debounced = useDebounce(query, 300);
  const error = useMemo(() => validateQuery(debounced), [debounced]);

  return (
    <Box component="section" aria-labelledby="query-form-title">
      <Stack spacing={2}>
        <Typography id="query-form-title" variant="h5">
          Ask FixIt AI
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Enter 10 to {QUERY_MAX_LENGTH} characters. You can paste detailed issues.
        </Typography>
        <TextField
          label="Support query"
          multiline
          minRows={5}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          error={Boolean(error)}
          helperText={error ?? `${query.length}/${QUERY_MAX_LENGTH}`}
          inputProps={{ maxLength: QUERY_MAX_LENGTH, "aria-describedby": "query-help" }}
          fullWidth
        />
        <Stack direction="row" gap={1} flexWrap="wrap">
          {EXAMPLES.map((example) => (
            <Chip key={example} label="Use example" onClick={() => setQuery(example)} />
          ))}
        </Stack>
        {error ? <Alert severity="warning">{error}</Alert> : null}
        <Button
          variant="contained"
          disabled={Boolean(error) || isLoading}
          onClick={() => onSubmit({ query: query.trim() })}
        >
          {isLoading ? "Submitting..." : "Submit Query"}
        </Button>
      </Stack>
    </Box>
  );
};
