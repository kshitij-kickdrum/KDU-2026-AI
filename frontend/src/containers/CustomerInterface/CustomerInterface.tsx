import Grid from "@mui/material/Grid";
import Paper from "@mui/material/Paper";

import FAQSection from "@/components/customer/FAQSection";
import QueryForm from "@/components/customer/QueryForm";
import ResponseDisplay from "@/components/customer/ResponseDisplay";
import { parseApiError } from "@/helpers/apiUtils";
import { useSubmitQueryMutation } from "@/store/api/queryApi";

export const CustomerInterface = () => {
  const [submitQuery, { data, isLoading, error }] = useSubmitQueryMutation();

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 2 }}>
          <QueryForm isLoading={isLoading} onSubmit={(payload) => submitQuery(payload)} />
        </Paper>
      </Grid>
      <Grid item xs={12} md={6}>
        <ResponseDisplay
          response={data}
          isLoading={isLoading}
          error={error ? parseApiError(error) : undefined}
        />
      </Grid>
      <Grid item xs={12}>
        <Paper sx={{ p: 2 }}>
          <FAQSection queryText={data?.response ?? ""} />
        </Paper>
      </Grid>
    </Grid>
  );
};
