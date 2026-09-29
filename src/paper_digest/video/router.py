from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from paper_digest.reader.store import get_paper
from paper_digest.video.agent import storyboard
from paper_digest.video.audio import audio_path, narration_state, start_narration
from paper_digest.video.schemas import NarrationState, Storyboard


router = APIRouter(
    prefix="/video",
    tags=["video"],
)


@router.post(
    "/{paper_id}/storyboard",
    response_model=Storyboard,
)
async def make_storyboard(
    paper_id: str,
) -> Storyboard:

    if get_paper(paper_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown paper {paper_id}")
    return await storyboard(paper_id)


@router.post(
    "/{paper_id}/narration",
    response_model=NarrationState,
    status_code=202,
)
async def make_narration(
    paper_id: str,
) -> NarrationState:

    if get_paper(paper_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown paper {paper_id}")
    return start_narration(paper_id)


@router.get(
    "/{paper_id}/narration",
    response_model=NarrationState,
)
async def narration(
    paper_id: str,
) -> NarrationState:

    return narration_state(paper_id)


@router.get("/{paper_id}/narration.mp3")
async def narration_audio(
    paper_id: str,
) -> FileResponse:

    if narration_state(paper_id).status != "ready":
        raise HTTPException(status_code=404, detail="Narration is not ready")
    return FileResponse(audio_path(paper_id), media_type="audio/mpeg")
