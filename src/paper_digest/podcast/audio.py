import asyncio
import logging
from pathlib import Path

import anthropic

from paper_digest.clients.tts import synthesize
from paper_digest.podcast.agent import podcast_script
from paper_digest.podcast.models import AudioStatus
from paper_digest.podcast.store import audio_status, set_audio_status


logger = logging.getLogger("uvicorn.error")

AUDIO_DIR = Path("data/podcasts")
VOICES = {"host": "am_michael", "author": "af_heart"}

_jobs: dict[str, asyncio.Task[None]] = {}
_errors: dict[str, str] = {}


def audio_path(paper_id: str) -> Path:
    return AUDIO_DIR / f"{paper_id}.mp3"


def current_status(paper_id: str) -> AudioStatus:
    job = _jobs.get(paper_id)
    if job is not None:
        if not job.done():
            return "running"
        # The row may not exist yet if the script step failed.
        if not audio_path(paper_id).exists():
            return "failed"
    status = audio_status(paper_id)
    if status == "ready" and not audio_path(paper_id).exists():
        return "none"
    if status == "running":
        # Left over from a restart mid-generation.
        return "failed"
    return status


def last_error(paper_id: str) -> str | None:
    return _errors.get(paper_id) if current_status(paper_id) == "failed" else None


def _describe(exc: Exception) -> str:
    if isinstance(exc, anthropic.AuthenticationError) or "credential" in str(exc):
        return "The Claude API key was rejected. Check ANTHROPIC_API_KEY in .env."
    if isinstance(exc, anthropic.APIError):
        return f"The Claude API failed: {exc.message}"
    return "Voicing the episode failed. See the API logs."


def start_audio(paper_id: str) -> AudioStatus:
    status = current_status(paper_id)
    if status in ("none", "failed"):
        _errors.pop(paper_id, None)
        _jobs[paper_id] = asyncio.create_task(_generate(paper_id))
        return "running"
    return status


async def _generate(paper_id: str) -> None:
    try:
        script = await podcast_script(paper_id)
        set_audio_status(paper_id, "running")
        turns = [(VOICES[line.speaker], line.text) for line in script.lines]
        await asyncio.to_thread(synthesize, turns, audio_path(paper_id))
        set_audio_status(paper_id, "ready")
    except Exception as exc:
        logger.exception("podcast audio failed for %s", paper_id)
        _errors[paper_id] = _describe(exc)
        set_audio_status(paper_id, "failed")
