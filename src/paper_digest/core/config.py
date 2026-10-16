from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Optional: the AI provider is normally set in the app (Admin → AI
    # provider). If nothing is saved there, an Anthropic key here is used.
    anthropic_api_key: str | None = None
    claude_model: str = "claude-haiku-4-5"
    summary_model: str = "claude-sonnet-5-5"
    database_url: str = "sqlite:///data/paper_digest.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
