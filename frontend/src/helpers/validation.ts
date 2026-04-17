import { QUERY_MAX_LENGTH, QUERY_MIN_LENGTH } from "@/config/constants";

export const validateQuery = (value: string): string | null => {
  const trimmed = value.trim();
  if (trimmed.length < QUERY_MIN_LENGTH) {
    return `Query must be at least ${QUERY_MIN_LENGTH} characters.`;
  }
  if (trimmed.length > QUERY_MAX_LENGTH) {
    return `Query must be at most ${QUERY_MAX_LENGTH} characters.`;
  }
  return null;
};
