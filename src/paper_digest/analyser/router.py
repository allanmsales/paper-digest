from fastapi import APIRouter

from paper_digest.analyser.agent import analyze_paper_content
from paper_digest.analyser.schemas import (
    PaperAnalysisRequest,
    PaperAnalyzerResponse,
)
from paper_digest.reader.pdf import parse_pdf_from_url


router = APIRouter(
    prefix="/analyser",
    tags=["analyser"],
)


@router.post(
    "/analyze",
    response_model=PaperAnalyzerResponse,
)
async def analyze(
    request: PaperAnalysisRequest,
) -> PaperAnalyzerResponse:

    paper_text = await parse_pdf_from_url(str(request.paper_url))

    return await analyze_paper_content(paper_text)
