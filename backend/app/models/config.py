from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Category = Literal["faq", "complaint", "booking"]
Complexity = Literal["low", "medium", "high"]
Provider = Literal["openrouter", "gemini"]


class AppSettingsModel(BaseModel):
    name: str
    environment: str
    log_level: str = "INFO"
    database_path: str


class FeatureFlags(BaseModel):
    enable_llm_classification_fallback: bool = True
    enable_cost_tracking: bool = True
    enable_budget_enforcement: bool = True
    enable_response_cache: bool = True
    enable_pre_summarization: bool = True


class Limits(BaseModel):
    rate_limit_requests_per_minute: int = 100


class SettingsConfig(BaseModel):
    app: AppSettingsModel
    features: FeatureFlags
    limits: Limits


class ModelDefinition(BaseModel):
    provider: Provider
    model_name: str
    input_cost_per_1k_tokens: Decimal = Field(ge=Decimal("0"))
    output_cost_per_1k_tokens: Decimal = Field(ge=Decimal("0"))
    max_tokens: int = Field(gt=0)
    timeout_seconds: int = Field(gt=0)


class ModelsConfig(BaseModel):
    models: dict[str, ModelDefinition]


class RoutingConfig(BaseModel):
    routing: dict[Category, dict[Complexity, str]]
    fallback: dict[str, str]


class BudgetPolicy(BaseModel):
    daily_limit_usd: Decimal = Field(gt=Decimal("0"))
    monthly_limit_usd: Decimal = Field(gt=Decimal("0"))
    warning_threshold_ratio: Decimal = Field(gt=Decimal("0"), le=Decimal("1"))


class BudgetConfig(BaseModel):
    budget: BudgetPolicy


class PromptCategoryRegistry(BaseModel):
    active_version: str
    available_versions: list[str]


class PromptRegistryConfig(BaseModel):
    registry: dict[str, PromptCategoryRegistry]


class PromptTemplateConfig(BaseModel):
    template: str


class RuntimeConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=False)

    settings: SettingsConfig
    models: ModelsConfig
    routing: RoutingConfig
    budget: BudgetConfig
    prompt_registry: PromptRegistryConfig
