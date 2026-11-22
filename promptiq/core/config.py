"""Application configuration and environment settings for PromptIQ."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration class loading from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    PROMPTIQ_ENV: Literal["development", "staging", "production", "test"] = "development"
    PROMPTIQ_LOG_LEVEL: str = "INFO"

    # API Settings (Default to loopback for security; set to 0.0.0.0 for external container binding)
    PROMPTIQ_API_HOST: str = "127.0.0.1"
    PROMPTIQ_API_PORT: int = 8000
    PROMPTIQ_SECRET_KEY: str = "promptiq_dev_secret_key_change_in_production_min_32_chars"
    PROMPTIQ_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    PROMPTIQ_REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days

    # CORS Settings (Explicit origins for Lovable frontend and local dev; wildcard disallow with credentials)
    PROMPTIQ_CORS_ORIGINS: str = (
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Returns parsed list of allowed CORS origins without wildcards."""
        if not self.PROMPTIQ_CORS_ORIGINS:
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
        return [o.strip() for o in self.PROMPTIQ_CORS_ORIGINS.split(",") if o.strip()]

    # Database
    # Default is SQLite for zero-config out-of-the-box local testing/dev
    # Set to PostgreSQL (postgresql+asyncpg://...) for production
    DATABASE_URL: str = "sqlite+aiosqlite:///./promptiq.db"

    # Storage
    STORAGE_LOCAL_DIR: str = "./storage"

    # ============================================================
    # Centrally Managed Zero-Price Inference Settings
    # NOTE: NO BYOK. No user API keys. Operator-level only.
    # ============================================================
    MANAGED_INFERENCE_PRIMARY_ROUTE: Literal["mock", "gemini", "groq", "openrouter"] = "mock"
    MANAGED_INFERENCE_ALLOW_MOCK_FALLBACK: bool = True
    ENFORCE_ZERO_PRICE_ONLY: bool = True  # Hard invariant: reject any non-zero price route

    # Operator credentials for free tiers (server-side only)
    OPERATOR_GEMINI_API_KEY: str = ""
    OPERATOR_GROQ_API_KEY: str = ""
    OPERATOR_OPENROUTER_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # Operator Free-Plan Attestation (Mandatory confirmation before executing live routes)
    OPERATOR_CONFIRMED_FREE_PLAN: bool = False
    OPERATOR_CONFIRMED_NO_PAID_UPGRADE: bool = False
    OPERATOR_CONFIRMED_HARD_STOP: bool = False
    PROMPTIQ_OPERATOR_FREE_TIER_CONFIRMED: bool = False

    @property
    def effective_groq_api_key(self) -> str:
        return self.OPERATOR_GROQ_API_KEY or self.GROQ_API_KEY

    @property
    def effective_gemini_api_key(self) -> str:
        return self.OPERATOR_GEMINI_API_KEY or self.GEMINI_API_KEY

    @property
    def is_operator_free_tier_confirmed(self) -> bool:
        return bool(
            self.PROMPTIQ_OPERATOR_FREE_TIER_CONFIRMED
            or (
                self.OPERATOR_CONFIRMED_FREE_PLAN
                and self.OPERATOR_CONFIRMED_NO_PAID_UPGRADE
                and self.OPERATOR_CONFIRMED_HARD_STOP
            )
        )

    # Capacity Governor & Fair Use Limits
    RATE_LIMIT_USER_REQUESTS_PER_HOUR: int = 60
    RATE_LIMIT_GLOBAL_CONCURRENCY: int = 10
    CAPACITY_GOVERNOR_ENABLED: bool = True

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_URL: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""

    @property
    def is_production(self) -> bool:
        return self.PROMPTIQ_ENV == "production"

    @property
    def is_test(self) -> bool:
        return self.PROMPTIQ_ENV == "test"


settings = Settings()
