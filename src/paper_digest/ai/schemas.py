from typing import Literal

from pydantic import BaseModel, Field

from paper_digest.clients.llm import AuthHeader, Provider


class AiSettingsIn(BaseModel):
    provider: Provider
    api_key: str | None = Field(
        default=None,
        description="Leave empty to keep the saved key.",
    )
    base_url: str | None = None
    auth_header: AuthHeader = "bearer"
    # Empty while the admin is still loading the model list.
    fast_model: str = ""
    smart_model: str = ""


class AiSettingsOut(BaseModel):
    configured: bool
    source: Literal["app", "env", "none"]
    provider: Provider | None = None
    base_url: str | None = None
    auth_header: AuthHeader = "bearer"
    fast_model: str | None = None
    smart_model: str | None = None
    has_key: bool = False
    key_hint: str | None = Field(default=None, description='e.g. "…a1b2"; never the key.')


class AiStatus(BaseModel):
    configured: bool
    provider: Provider | None = None


class Preset(BaseModel):
    id: str
    label: str
    provider: Provider
    base_url: str | None = None
    auth_header: AuthHeader = "bearer"
    fast_model: str = ""
    smart_model: str = ""
    help: str


class TestResult(BaseModel):
    ok: bool
    message: str


class ModelList(BaseModel):
    models: list[str]
