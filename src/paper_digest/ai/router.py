from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from paper_digest.ai.presets import PRESETS
from paper_digest.ai.schemas import (
    AiSettingsIn,
    AiSettingsOut,
    AiStatus,
    ModelList,
    Preset,
    TestResult,
)
from paper_digest.ai.store import check_models, describe, draft_config, save_settings
from paper_digest.clients.llm import current_config, describe_error, list_models, test_connection
from paper_digest.users.auth import current_user, require_admin
from paper_digest.users.models import User


router = APIRouter(
    prefix="/ai",
    tags=["ai"],
)


@router.get("/status", response_model=AiStatus)
async def status(_: Annotated[User, Depends(current_user)]) -> AiStatus:
    config = current_config()
    return AiStatus(configured=config is not None, provider=config.provider if config else None)


@router.get("/presets", response_model=list[Preset], dependencies=[Depends(require_admin)])
async def presets() -> list[Preset]:
    return PRESETS


@router.get("/settings", response_model=AiSettingsOut, dependencies=[Depends(require_admin)])
def get_settings() -> AiSettingsOut:
    return describe()


@router.put("/settings", response_model=AiSettingsOut, dependencies=[Depends(require_admin)])
def put_settings(request: AiSettingsIn) -> AiSettingsOut:
    try:
        save_settings(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return describe()


@router.post("/test", response_model=TestResult, dependencies=[Depends(require_admin)])
async def test(request: AiSettingsIn) -> TestResult:
    """Tries both models with the (possibly unsaved) settings."""
    config = draft_config(request)
    try:
        check_models(config)
    except ValueError as exc:
        return TestResult(ok=False, message=str(exc))
    try:
        for tier in ("fast", "smart"):
            await test_connection(config, tier)
    except Exception as exc:  # report any provider error to the admin
        return TestResult(ok=False, message=f"{tier} model: {describe_error(exc, config)}")
    return TestResult(ok=True, message="Both models answered.")


@router.post("/models", response_model=ModelList, dependencies=[Depends(require_admin)])
async def models(request: AiSettingsIn) -> ModelList:
    config = draft_config(request)
    try:
        return ModelList(models=await list_models(config))
    except Exception as exc:  # report any provider error to the admin
        raise HTTPException(
            status_code=400, detail=f"Could not list models: {describe_error(exc, config)}"
        ) from exc
