from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from paper_digest.analyser.router import router as analyser_router
from paper_digest.explainer.router import router as explainer_router
from paper_digest.feed.router import router as feed_router
from paper_digest.podcast.router import router as podcast_router
from paper_digest.reader.router import router as reader_router
from paper_digest.core.db import init_db
from paper_digest.splitter.router import router as splitter_router
from paper_digest.users.auth import current_user
from paper_digest.users.router import router as users_router
from paper_digest.users.store import claim_unowned_rows
from paper_digest.video.router import router as video_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Routers import their domain models, so every table is registered here.
    init_db()
    claim_unowned_rows(["signal", "postview"])
    yield


app = FastAPI(
    title="Paper Digest",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok"}

# Everything except /users (login) needs a signed-in user.
signed_in = [Depends(current_user)]

app.include_router(users_router)
app.include_router(reader_router, dependencies=signed_in)
app.include_router(analyser_router, dependencies=signed_in)
app.include_router(splitter_router, dependencies=signed_in)
app.include_router(explainer_router, dependencies=signed_in)
app.include_router(feed_router, dependencies=signed_in)
app.include_router(podcast_router, dependencies=signed_in)
app.include_router(video_router, dependencies=signed_in)
