from fastapi import APIRouter, BackgroundTasks, HTTPException

from paper_digest.explainer.agent import (
    answer_question,
    check_understanding,
    explain_by_analogy,
    explain_selection,
    register_paper,
    summarize_paper,
    warm_paper,
)
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
) -> ExplainResponse:

    return await explain_selection(request)


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
) -> CheckResponse:

    try:
        return await check_understanding(
            request.paper_text,
            request.section,
            request.answer,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/ask",
    response_model=AskResponse,
)
async def ask(
    request: AskRequest,
) -> AskResponse:

    return await answer_question(request)


@router.post(
    "/warm",
    status_code=202,
    response_model=WarmResponse,
)
async def warm(
    request: PaperRequest,
    background_tasks: BackgroundTasks,
) -> WarmResponse:

    key = register_paper(request.paper_text, request.source)
    background_tasks.add_task(warm_paper, request.paper_text)

    return WarmResponse(status="warming", paper_id=key)
