from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from paper_digest.explainer.agent import (
    answer_question,
    check_understanding,
    explain_by_analogy,
    explain_selection,
    register_paper,
    summarize_paper,
    warm_paper,
)
from paper_digest.explainer.store import list_checks, list_lookups
from paper_digest.reader.store import record_open
from paper_digest.users.auth import current_user
from paper_digest.users.models import User
from paper_digest.explainer.schemas import (
    AnalogyRequest,
    AnalogyResponse,
    AskRequest,
    AskResponse,
    CheckRequest,
    CheckResponse,
    ExplainRequest,
    ExplainResponse,
    PaperRequest,
    SavedCheck,
    SavedLookup,
    SummaryResponse,
    WarmResponse,
)


router = APIRouter(
    prefix="/explainer",
    tags=["explainer"],
)


@router.post(
    "/explain",
    response_model=ExplainResponse,
)
async def explain(
    request: ExplainRequest,
    user: Annotated[User, Depends(current_user)],
) -> ExplainResponse:

    return await explain_selection(request, user.id)


@router.post(
    "/summary",
    response_model=SummaryResponse,
)
async def summary(
    request: PaperRequest,
) -> SummaryResponse:

    return await summarize_paper(request.paper_text)


@router.post(
    "/analogy",
    response_model=AnalogyResponse,
)
async def analogy(
    request: AnalogyRequest,
) -> AnalogyResponse:

    return await explain_by_analogy(request.paper_text, request.subject)


@router.post(
    "/check",
    response_model=CheckResponse,
)
async def check(
    request: CheckRequest,
    user: Annotated[User, Depends(current_user)],
) -> CheckResponse:

    try:
        return await check_understanding(
            request.paper_text,
            request.section,
            request.answer,
            user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/ask",
    response_model=AskResponse,
)
async def ask(
    request: AskRequest,
    user: Annotated[User, Depends(current_user)],
) -> AskResponse:

    return await answer_question(request, user.id)


@router.post(
    "/warm",
    status_code=202,
    response_model=WarmResponse,
)
async def warm(
    request: PaperRequest,
    background_tasks: BackgroundTasks,
    user: Annotated[User, Depends(current_user)],
) -> WarmResponse:

    key = register_paper(request.paper_text, request.source)
    record_open(user.id, key, request.source)
    background_tasks.add_task(warm_paper, request.paper_text)

    return WarmResponse(status="warming", paper_id=key)


@router.get(
    "/{paper_id}/lookups",
    response_model=list[SavedLookup],
)
async def lookups(
    paper_id: str,
    user: Annotated[User, Depends(current_user)],
) -> list[SavedLookup]:

    return list_lookups(user.id, paper_id)


@router.get(
    "/{paper_id}/checks",
    response_model=list[SavedCheck],
)
async def checks(
    paper_id: str,
    user: Annotated[User, Depends(current_user)],
) -> list[SavedCheck]:

    return list_checks(user.id, paper_id)
