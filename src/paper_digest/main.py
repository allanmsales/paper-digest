from fastapi import FastAPI

from paper_digest.analyser.router import router as analyser_router
from paper_digest.explainer.router import router as explainer_router
from paper_digest.reader.router import router as reader_router
from paper_digest.splitter.router import router as splitter_router

app = FastAPI(
    title="Paper Digest",
    version="0.1.0"
)


@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(reader_router)
app.include_router(analyser_router)
app.include_router(splitter_router)
app.include_router(explainer_router)
