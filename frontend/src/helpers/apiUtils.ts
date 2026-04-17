export const parseApiError = (error: unknown): string => {
  if (typeof error === "string") {
    return error;
  }
  if (error && typeof error === "object" && "data" in error) {
    const data = (error as { data?: { detail?: string } }).data;
    if (data?.detail) {
      return data.detail;
    }
  }
  return "Something went wrong. Please try again.";
};
