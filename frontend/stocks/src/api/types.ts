export type Currency = 'USD' | 'INR' | 'EUR'

export interface HoldingModel {
  symbol: string
  quantity: number
  avg_buy_price: number
}

export interface RunRequest {
  thread_id: string
  portfolio: HoldingModel[]
  currency: Currency
  symbol: string
  prompt?: string
}

export interface RunResponse {
  status: 'completed' | 'awaiting_approval'
  thread_id: string
  portfolio_total_usd?: number | null
  portfolio_total_converted?: number | null
  currency?: string | null
  trade_log?: string[] | null
  pending_action?: 'buy' | 'sell' | null
}

export interface ApproveRequest {
  thread_id: string
  approved: boolean
}

export interface ApproveResponse {
  status: 'completed' | 'cancelled'
  thread_id: string
  trade_log: string[]
  portfolio?: HoldingModel[] | null
  portfolio_total_usd?: number | null
  portfolio_total_converted?: number | null
  currency?: Currency | null
}

export interface AgentStateSnapshot {
  user_prompt?: string | null
  messages?: unknown[]
  portfolio_total_usd?: number
  portfolio_total_converted?: number | null
  currency?: Currency
  exchange_rate?: number | null
  pending_action?: 'buy' | 'sell'
  action_approved?: boolean
  trade_log?: string[]
  error?: string | null
  [key: string]: unknown
}

export interface StateResponse {
  thread_id: string
  status: 'completed' | 'awaiting_approval' | 'in_progress'
  state: AgentStateSnapshot
}

export interface SessionSummary {
  session_ref: string
  status: 'completed' | 'awaiting_approval' | 'in_progress' | 'cancelled'
  updated_at: string
  portfolio_total_usd?: number | null
  portfolio_total_converted?: number | null
  currency?: Currency | null
}

export interface SessionsResponse {
  sessions: SessionSummary[]
}

export interface SessionStateResponse {
  session_ref: string
  status: 'completed' | 'awaiting_approval' | 'in_progress' | 'cancelled'
  state: AgentStateSnapshot
}

export interface HealthResponse {
  status: 'ok'
  version: string
}

export interface SymbolSearchResult {
  symbol: string
  description: string
  price?: number | null
}

export interface ApiErrorResponse {
  code: string
  message: string
}
