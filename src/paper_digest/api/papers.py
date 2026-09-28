from fastapi import APIRouter

from paper_digest.schemas.paper import (
    PaperAnalysisRequest,
    PaperAnalysisResponse,
)
from paper_digest.services.paper_analysis import analyze_paper


router = APIRouter(
    prefix="/papers",
    tags=["papers"],
)


@router.post(
    "/analyze",
    response_model=PaperAnalysisResponse,
)
async def analyze(
    request: PaperAnalysisRequest,
) -> PaperAnalysisResponse:

    return await analyze_paper(
        str(request.paper_url)
    )