from fastapi import FastAPI

from paper_digest.api.papers import router as papers_router

app = FastAPI(
    title="Paper Digest",
    version="0.1.0"
)


@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(papers_router)