import asyncio
import logging
import re
from pathlib import Path

import anthropic

from paper_digest.clients.tts import synthesize
from paper_digest.video.agent import storyboard
from paper_digest.video.schemas import (
    Narration,
    NarrationState,
    SceneNarration,
    TimedSentence,
)
from paper_digest.video.store import narration_row, set_narration


logger = logging.getLogger("uvicorn.error")

AUDIO_DIR = Path("data/videos")
VOICE = "af_heart"
SENTENCE_PAUSE = 0.35
SCENE_PAUSE = 1.0

_jobs: dict[str, asyncio.Task[None]] = {}
_errors: dict[str, str] = {}

# Same rule as the web player's splitSentences: a sentence ends at . ! or ?
# (optionally closed by a quote or bracket) followed by whitespace, so
# decimals like 0.58 stay whole.
_BOUNDARY = re.compile(r"""(?<=[.!?])\s+|(?<=[.!?]["')\]])\s+""")


def split_sentences(text: str) -> list[str]:
    parts = [part.strip() for part in _BOUNDARY.split(text.strip())]
    return [part for part in parts if part] or [text.strip()]


def audio_path(paper_id: str) -> Path:
    return AUDIO_DIR / f"{paper_id}.mp3"


def narration_state(paper_id: str) -> NarrationState:
    job = _jobs.get(paper_id)
    if job is not None and not job.done():
        return NarrationState(status="running")
    status, timings = narration_row(paper_id)
    if status == "ready" and (timings is None or not audio_path(paper_id).exists()):
        status = "none"
    if status == "running":
        # Left over from a restart mid-generation.
        status = "failed"
    detail = _errors.get(paper_id) if status == "failed" else None
    return NarrationState(
        status=status, detail=detail, narration=timings if status == "ready" else None
    )


def start_narration(paper_id: str) -> NarrationState:
    state = narration_state(paper_id)
    if state.status in ("none", "failed"):
        _errors.pop(paper_id, None)
        _jobs[paper_id] = asyncio.create_task(_generate(paper_id))
        return NarrationState(status="running")
    return state


async def _generate(paper_id: str) -> None:
    try:
        board = await storyboard(paper_id)
        set_narration(paper_id, "running")

        scene_sentences = [split_sentences(scene.narration) for scene in board.scenes]
        segments = [
            (VOICE, text, SCENE_PAUSE if index == len(sentences) - 1 else SENTENCE_PAUSE)
            for sentences in scene_sentences
            for index, text in enumerate(sentences)
        ]
        spans = await asyncio.to_thread(synthesize, segments, audio_path(paper_id))

        scenes: list[SceneNarration] = []
        cursor = 0
        for sentences in scene_sentences:
            timed = [
                TimedSentence(text=text, start=start, end=end)
                for text, (start, end) in zip(sentences, spans[cursor : cursor + len(sentences)])
            ]
            cursor += len(sentences)
            scenes.append(SceneNarration(start=timed[0].start, end=timed[-1].end, sentences=timed))
        # Each scene runs until the next one starts, so its pause stays with it.
        for current, following in zip(scenes, scenes[1:]):
            current.end = following.start
        total = scenes[-1].end + SCENE_PAUSE
        scenes[-1].end = total

        set_narration(paper_id, "ready", Narration(total=total, scenes=scenes))
    except Exception as exc:
        logger.exception("video narration failed for %s", paper_id)
        _errors[paper_id] = (
            "Claude is having problems right now. Try again later."
            if isinstance(exc, anthropic.APIError)
            else "Recording the narration failed. See the API logs."
        )
        set_narration(paper_id, "failed")
