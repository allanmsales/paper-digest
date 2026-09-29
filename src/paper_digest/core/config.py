from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    anthropic_api_key: str
    claude_model: str
    # Stronger model for tasks that need careful plain-language rewriting.
    summary_model: str = "claude-sonnet-5-5"
    database_url: str = "sqlite:///data/paper_digest.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()