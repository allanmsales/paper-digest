from fastapi import APIRouter, HTTPException

from paper_digest.feed.agent import next_session, record_view, start_build
from paper_digest.feed.schemas import FeedSession, ViewRequest


router = APIRouter(
    prefix="/feed",
    tags=["feed"],
)


@router.post("/{paper_id}/build", status_code=202)
async def build(
    paper_id: str,
) -> dict[str, str]:

    return {"status": start_build(paper_id, retry=True)}


@router.get(
    "/{paper_id}/session",
    response_model=FeedSession,
)
async def session(
    paper_id: str,
) -> FeedSession:

    return await next_session(paper_id)


@router.post("/view", status_code=204)
async def view(
    request: ViewRequest,
) -> None:

    try:
        record_view(request.post_id, request.correct)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
