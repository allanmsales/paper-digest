from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from paper_digest.podcast.agent import podcast_script
from paper_digest.podcast.audio import audio_path, current_status, last_error, start_audio
from paper_digest.podcast.schemas import AudioState, Script
from paper_digest.reader.store import get_paper


router = APIRouter(
    prefix="/podcast",
    tags=["podcast"],
)


def _require_paper(paper_id: str) -> None:
    if get_paper(paper_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown paper {paper_id}")


@router.post(
    "/{paper_id}/script",
    response_model=Script,
)
async def script(
    paper_id: str,
) -> Script:

    _require_paper(paper_id)
    return await podcast_script(paper_id)


@router.post(
    "/{paper_id}/audio",
    response_model=AudioState,
    status_code=202,
)
async def generate_audio(
    paper_id: str,
) -> AudioState:

    _require_paper(paper_id)
    return AudioState(status=start_audio(paper_id))


@router.get(
    "/{paper_id}/status",
    response_model=AudioState,
)
async def status(
    paper_id: str,
) -> AudioState:

    return AudioState(status=current_status(paper_id), detail=last_error(paper_id))


@router.get("/{paper_id}/audio.mp3")
async def audio(
    paper_id: str,
) -> FileResponse:

    if current_status(paper_id) != "ready":
        raise HTTPException(status_code=404, detail="Podcast audio is not ready")
    return FileResponse(audio_path(paper_id), media_type="audio/mpeg")
