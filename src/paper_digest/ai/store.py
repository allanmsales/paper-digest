from datetime import UTC, datetime

from paper_digest.ai.models import AiSettings
from paper_digest.ai.schemas import AiSettingsIn, AiSettingsOut
from paper_digest.clients.llm import LlmConfig, configure
from paper_digest.core.config import settings
from paper_digest.core.db import db_session


def _row() -> AiSettings | None:
    with db_session() as session:
        return session.get(AiSettings, 1)


def _from_row(row: AiSettings) -> LlmConfig:
    return LlmConfig(
        provider=row.provider,
        api_key=row.api_key,
        base_url=row.base_url,
        auth_header=row.auth_header,
        fast_model=row.fast_model,
        smart_model=row.smart_model,
    )


def _from_env() -> LlmConfig | None:
    if not settings.anthropic_api_key:
        return None
    return LlmConfig(
        provider="anthropic",
        api_key=settings.anthropic_api_key,
        fast_model=settings.claude_model,
        smart_model=settings.summary_model,
    )


def load_config() -> LlmConfig | None:
    """Settings saved in the app win; an Anthropic key in .env is the fallback."""
    row = _row()
    return _from_row(row) if row else _from_env()


def apply_saved_config() -> None:
    configure(load_config())


def draft_config(request: AiSettingsIn) -> LlmConfig:
    """`request` as a config; an empty key reuses the saved one."""
    key = (request.api_key or "").strip()
    if not key:
        current = load_config()
        key = current.api_key if current and current.provider == request.provider else ""
    return LlmConfig(
        provider=request.provider,
        api_key=key,
        base_url=(request.base_url or "").strip() or None,
        auth_header=request.auth_header,
        fast_model=request.fast_model.strip(),
        smart_model=request.smart_model.strip(),
    )


def check_models(config: LlmConfig) -> None:
    if not config.fast_model or not config.smart_model:
        raise ValueError("Pick a fast and a smart model.")


def save_settings(request: AiSettingsIn) -> None:
    config = draft_config(request)
    check_models(config)
    if not config.api_key and config.provider != "compatible":
        raise ValueError("Add an API key.")
    if config.provider == "compatible" and not config.base_url:
        raise ValueError("Add the API's base URL.")
    with db_session() as session:
        session.merge(
            AiSettings(
                id=1,
                provider=config.provider,
                api_key=config.api_key,
                base_url=config.base_url,
                auth_header=config.auth_header,
                fast_model=config.fast_model,
                smart_model=config.smart_model,
                updated_at=datetime.now(UTC),
            )
        )
        session.commit()
    configure(config)


def describe() -> AiSettingsOut:
    row = _row()
    config = load_config()
    if config is None:
        return AiSettingsOut(configured=False, source="none")
    return AiSettingsOut(
        configured=True,
        source="app" if row else "env",
        provider=config.provider,
        base_url=config.base_url,
        auth_header=config.auth_header,
        fast_model=config.fast_model,
        smart_model=config.smart_model,
        has_key=bool(config.api_key),
        # Only long keys get a hint, so a short key is never revealed.
        key_hint=f"…{config.api_key[-4:]}" if len(config.api_key) > 8 else None,
    )
