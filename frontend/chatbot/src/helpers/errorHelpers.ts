import type { ApiErrorCode } from '../types';

export const ERROR_MESSAGES: Record<ApiErrorCode, string> = {
  USER_NOT_FOUND: 'User not found. Please reload and sign in again.',
  RATE_LIMIT_EXCEEDED: 'Too many requests. Please wait a minute and try again.',
  UPSTREAM_RATE_LIMITED: 'AI provider is busy right now. Please retry in a few seconds.',
  UPSTREAM_SERVICE_UNAVAILABLE: 'AI provider is temporarily unavailable. Please try again shortly.',
  UNSUPPORTED_FORMAT: 'Only JPG and PNG images are supported',
  IMAGE_TOO_LARGE: 'Image must be under 10MB',
  PARSE_ERROR: 'AI response could not be parsed. Please try again.',
  INVALID_NAME: 'Invalid name. Please reload and try again.',
  INVALID_LOCATION: 'Invalid location. Please reload and try again.',
  INVALID_AGE: 'Invalid age. Please reload and try again.',
  TOOL_CALL_FAILED: 'A tool call failed. Please try again.',
  AGENT_MAX_ITERATIONS: 'The agent reached its limit. Try a simpler question.',
};

export function getErrorMessage(
  code?: string,
  fallback = 'Something went wrong. Please try again.',
): string {
  if (!code) return fallback;
  return ERROR_MESSAGES[code as ApiErrorCode] ?? fallback;
}
