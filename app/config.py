from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram
    bot_token: str

    # LLM
    llm_provider: str = "groq"
    llm_temperature: float = 0.3

    # Groq
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Admin
    admin_ids: list[int] = []

    # Database
    database_url: str = "sqlite+aiosqlite:///./mindlint.db"

    # Logging
    log_level: str = "INFO"

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            v = v.strip("[]")
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v


settings = Settings()
