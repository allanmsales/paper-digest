from fastapi import APIRouter

from paper_digest.analyser.schemas import PaperAnalysisRequest
from paper_digest.splitter.schemas import PaperAnalysisResponse
from paper_digest.splitter.service import analyze_paper


router = APIRouter(
    prefix="/splitter",
    tags=["splitter"],
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