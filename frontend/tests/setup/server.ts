import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";

export const server = setupServer(
  http.post("/api/query", async () =>
    HttpResponse.json({
      query_id: "q-1",
      response: "Mock response",
      category: "faq",
      complexity: "low",
      model_used: "gemini-flash-lite",
      prompt_version: "v1",
      classification_method: "rule_based",
      tokens: { prompt: 10, completion: 20 },
      cost_usd: 0.01,
      cache_hit: false,
      was_summarized: false,
      budget_status: { daily_remaining_usd: 0.99, budget_fallback_active: false },
      latency_ms: 100,
    }),
  ),
);
