"""Local text-to-speech with Kokoro (ONNX, CPU). Model files are downloaded
to data/models on first use."""

import logging
import threading
from pathlib import Path

import httpx
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro


logger = logging.getLogger("uvicorn.error")

MODEL_DIR = Path("data/models")
MODEL_URLS = {
    "kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
    "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
}

_kokoro: Kokoro | None = None
_lock = threading.Lock()


def _download(name: str, url: str) -> Path:
    path = MODEL_DIR / name
    if not path.exists():
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("downloading %s", url)
        partial = path.with_suffix(".part")
        with httpx.stream("GET", url, follow_redirects=True, timeout=60) as response:
            response.raise_for_status()
            with partial.open("wb") as file:
                for chunk in response.iter_bytes(1 << 20):
                    file.write(chunk)
        partial.rename(path)
    return path


def _get_kokoro() -> Kokoro:
    global _kokoro
    with _lock:
        if _kokoro is None:
            paths = [_download(name, url) for name, url in MODEL_URLS.items()]
            _kokoro = Kokoro(str(paths[0]), str(paths[1]))
        return _kokoro


def synthesize(
    segments: list[tuple[str, str, float]], out_path: Path
) -> list[tuple[float, float]]:
    """Speaks each (voice, text, pause_after_seconds) segment and writes them
    to one MP3. Returns each segment's (start, end) in seconds, so a player
    can sync to it. Blocking and CPU-bound: run it in a thread."""

    kokoro = _get_kokoro()
    chunks: list[np.ndarray] = []
    spans: list[tuple[float, float]] = []
    sample_rate = 24000
    position = 0
    for voice, text, pause_seconds in segments:
        samples, sample_rate = kokoro.create(text, voice=voice)
        spans.append((position / sample_rate, (position + len(samples)) / sample_rate))
        silence = np.zeros(int(pause_seconds * sample_rate), dtype=np.float32)
        chunks += [samples, silence]
        position += len(samples) + len(silence)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    partial = out_path.with_suffix(".part.mp3")
    sf.write(partial, np.concatenate(chunks), sample_rate, format="MP3")
    partial.rename(out_path)
    return spans
