// ─── User & Auth ─────────────────────────────────────────────────────────────

export type Style = 'expert' | 'child';

export interface UserProfile {
  user_id: string;
  name: string;
  location: string;
  age: number;
  style: Style;
}

export interface RegisterRequest {
  name: string;
  location: string;
  age: number;
}

export interface RegisterResponse extends UserProfile {}

// ─── Chat ────────────────────────────────────────────────────────────────────

export type MessageRole = 'human' | 'ai';

export type IntentType = 'weather' | 'image' | 'general';

export interface WeatherResponse {
  temperature: string;
  feels_like: string;
  summary: string;
  location: string;
  advice: string;
}

export interface ImageResponse {
  description: string;
  objects_detected: string[];
  scene_type: string;
  confidence: 'high' | 'medium' | 'low';
}

export interface GeneralResponse {
  answer: string;
  follow_up: string | null;
}

export type ParsedResponse = WeatherResponse | ImageResponse | GeneralResponse;

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  // AI message metadata
  model_used?: string;
  tool_used?: string | null;
  style_applied?: Style | null;
  response?: ParsedResponse;
  intent?: IntentType;
  timestamp: number;
}

export interface ChatRequest {
  user_id: string;
  session_id: string;
  message: string;
  style?: Style;
}

export interface ChatApiResponse {
  session_id: string;
  response: ParsedResponse;
  model_used: string;
  tool_used: string | null;
  style_applied: Style | null;
}

// ─── Image ───────────────────────────────────────────────────────────────────

export interface ImageApiResponse {
  session_id: string;
  response: ImageResponse;
  model_used: string;
  tool_used: string | null;
  style_applied: Style | null;
}

// ─── Session History ──────────────────────────────────────────────────────────

export interface HistoryMessage {
  role: MessageRole;
  content: string;
}

export interface HistoryResponse {
  session_id: string;
  message_count: number;
  messages: HistoryMessage[];
}

export interface DeleteSessionRequest {
  user_id: string;
  session_id: string;
}

export interface SessionSummary {
  session_id: string;
  title: string;
  preview: string;
  created_at: number;
  updated_at: number;
  message_count: number;
}

export interface SessionListResponse {
  sessions: SessionSummary[];
}

// ─── API Error ───────────────────────────────────────────────────────────────

export type ApiErrorCode =
  | 'USER_NOT_FOUND'
  | 'RATE_LIMIT_EXCEEDED'
  | 'UPSTREAM_RATE_LIMITED'
  | 'UPSTREAM_SERVICE_UNAVAILABLE'
  | 'UNSUPPORTED_FORMAT'
  | 'IMAGE_TOO_LARGE'
  | 'PARSE_ERROR'
  | 'INVALID_NAME'
  | 'INVALID_LOCATION'
  | 'INVALID_AGE'
  | 'TOOL_CALL_FAILED'
  | 'AGENT_MAX_ITERATIONS';

export interface ApiError {
  code: ApiErrorCode;
  message: string;
}

// ─── Toast ────────────────────────────────────────────────────────────────────

export type ToastVariant = 'error' | 'warning' | 'success';

export interface Toast {
  id: string;
  message: string;
  variant: ToastVariant;
}
