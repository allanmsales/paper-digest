from typing import Annotated

from fastapi import APIRouter, Depends

from paper_digest.progress.agent import assess
from paper_digest.progress.schemas import (
    AssessmentOut,
    HeardRequest,
    KnowledgeMap,
    MilestoneRequest,
    Progress,
)
from paper_digest.progress.service import knowledge_map, progress
from paper_digest.progress.store import add_heard, add_milestone, latest_assessment
from paper_digest.users.auth import current_user
from paper_digest.users.models import User


router = APIRouter(
    prefix="/progress",
    tags=["progress"],
)


@router.get("/{paper_id}", response_model=Progress)
async def get_progress(
    paper_id: str,
    user: Annotated[User, Depends(current_user)],
) -> Progress:

    return progress(paper_id, user.id)


@router.post("/{paper_id}/heard", status_code=204)
async def heard(
    paper_id: str,
    request: HeardRequest,
    user: Annotated[User, Depends(current_user)],
) -> None:

    add_heard(user.id, paper_id, request.kind, request.buckets, request.total)


@router.get("/{paper_id}/map", response_model=KnowledgeMap)
async def get_map(
    paper_id: str,
    user: Annotated[User, Depends(current_user)],
) -> KnowledgeMap:

    return knowledge_map(paper_id, user.id)


@router.get("/{paper_id}/assessment", response_model=AssessmentOut | None)
async def get_assessment(
    paper_id: str,
    user: Annotated[User, Depends(current_user)],
) -> AssessmentOut | None:

    return latest_assessment(user.id, paper_id)


@router.post("/{paper_id}/assessment", response_model=AssessmentOut)
async def make_assessment(
    paper_id: str,
    user: Annotated[User, Depends(current_user)],
) -> AssessmentOut:

    return await assess(paper_id, user.id)


@router.post("/{paper_id}/milestone", status_code=204)
async def milestone(
    paper_id: str,
    request: MilestoneRequest,
    user: Annotated[User, Depends(current_user)],
) -> None:

    add_milestone(user.id, paper_id, request.item)
