export interface QuerySubmission {
  query: string;
  session_id?: string;
  override_category?: "faq" | "complaint" | "booking";
  override_complexity?: "low" | "medium" | "high";
}

export interface QueryResponse {
  query_id: string;
  response: string;
  category: string;
  complexity: string;
  model_used: string;
  prompt_version: string;
  classification_method: string;
  tokens: {
    prompt: number;
    completion: number;
  };
  cost_usd: number;
  cache_hit: boolean;
  was_summarized: boolean;
  budget_status: {
    daily_remaining_usd: number;
    budget_fallback_active: boolean;
  };
  latency_ms: number;
}

export interface AdminStats {
  daily_stats: {
    total_queries: number;
    total_cost_usd: number;
    by_category: Record<string, { queries: number; cost_usd: number }>;
    by_model: Record<string, { queries: number; cost_usd: number }>;
  };
  monthly_stats: {
    total_queries: number;
    total_cost_usd: number;
    by_category: Record<string, { queries: number; cost_usd: number }>;
    by_model: Record<string, { queries: number; cost_usd: number }>;
  };
  cache_stats: {
    hit_rate: number;
    total_entries: number;
  };
}

export interface PromptRegistry {
  registry: Record<
    string,
    {
      active_version: string;
      available_versions: string[];
    }
  >;
}

export interface ActivatePromptRequest {
  category: string;
  version: string;
}

export interface ActivatePromptResponse {
  message: string;
  category: string;
  previous_version: string;
  new_version: string;
}

export interface ConfigReloadResponse {
  message: string;
  reloaded_files: string[];
}

export interface HealthResponse {
  status: string;
  database: string;
  config: string;
  timestamp: string;
}
