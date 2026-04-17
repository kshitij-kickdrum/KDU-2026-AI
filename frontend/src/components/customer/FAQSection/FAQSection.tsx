import { useMemo, useState } from "react";

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";

import { FAQ_SEARCH_DEBOUNCE_MS } from "@/config/constants";
import { useDebounce } from "@/hooks/useDebounce";
import type { FAQQuestion } from "@/types/ui";

const FAQS: FAQQuestion[] = [
  {
    id: "1",
    question: "How quickly can someone visit my home?",
    answer: "Most slots are available within 2 to 6 hours depending on location.",
    category: "booking",
    popularity: 9,
  },
  {
    id: "2",
    question: "How do refunds work if service quality was poor?",
    answer: "Submit a complaint with booking details and we review within 24 hours.",
    category: "complaint",
    popularity: 8,
  },
  {
    id: "3",
    question: "Can I book recurring cleaning every week?",
    answer: "Yes, recurring plans can be set through booking support.",
    category: "faq",
    popularity: 7,
  },
];

interface FAQSectionProps {
  queryText: string;
  onTrackInteraction?: (event: string, payload: Record<string, string>) => void;
}

export const FAQSection = ({ queryText, onTrackInteraction }: FAQSectionProps) => {
  const [search, setSearch] = useState("");
  const debounced = useDebounce(search, FAQ_SEARCH_DEBOUNCE_MS);

  const filtered = useMemo(() => {
    const term = debounced.trim().toLowerCase();
    if (!term) {
      return FAQS;
    }
    return FAQS.filter(
      (item) =>
        item.question.toLowerCase().includes(term) ||
        item.answer.toLowerCase().includes(term) ||
        item.category.toLowerCase().includes(term),
    );
  }, [debounced]);

  const suggested = useMemo(() => {
    const source = queryText.toLowerCase();
    return FAQS.filter(
      (item) => source.includes(item.category) || source.includes(item.question.toLowerCase().split(" ")[0]),
    ).slice(0, 2);
  }, [queryText]);

  return (
    <Box component="section" aria-labelledby="faq-title">
      <Stack spacing={2}>
        <Typography id="faq-title" variant="h6">
          Frequently Asked Questions
        </Typography>
        <TextField
          label="Search FAQs"
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            onTrackInteraction?.("faq_search", { term: event.target.value });
          }}
        />
        {filtered.length === 0 ? <Alert severity="info">No FAQ matches found.</Alert> : null}
        {filtered.map((item) => (
          <Accordion key={item.id} onChange={() => onTrackInteraction?.("faq_view", { id: item.id })}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>{item.question}</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">{item.answer}</Typography>
            </AccordionDetails>
          </Accordion>
        ))}
        {suggested.length > 0 ? (
          <Box>
            <Typography variant="subtitle2">Suggested by your query</Typography>
            {suggested.map((item) => (
              <Typography key={item.id} variant="body2">
                - {item.question}
              </Typography>
            ))}
          </Box>
        ) : null}
      </Stack>
    </Box>
  );
};
