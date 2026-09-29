from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from paper_digest.feed.agent import next_session, record_view, start_build
from paper_digest.feed.schemas import FeedSession, ViewRequest
from paper_digest.users.auth import current_user
from paper_digest.users.models import User


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
    user: Annotated[User, Depends(current_user)],
) -> FeedSession:

    return await next_session(paper_id, user.id)


@router.post("/view", status_code=204)
async def view(
    request: ViewRequest,
    user: Annotated[User, Depends(current_user)],
) -> None:

    try:
        record_view(request.post_id, request.correct, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
