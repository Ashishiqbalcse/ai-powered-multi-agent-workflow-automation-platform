from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Multi-Agent Workflow Automation"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./multi_agent.db"
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"

    serper_api_key: str | None = None
    tavily_api_key: str | None = None

    vector_backend: str = "chroma"
    chroma_path: str = "./.chroma"
    pinecone_api_key: str | None = None
    pinecone_index: str = "agent-memory"

    max_iterations: int = 8
    agent_timeout_seconds: int = 120
    default_budget_usd: float = 2.0
    cost_warn_threshold: float = 0.8
    code_sandbox_timeout_seconds: int = 10

    allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

