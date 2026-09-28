from fastapi import APIRouter, HTTPException, Query, Response

from paper_digest.reader.pdf import PDFParserError, download_pdf


router = APIRouter(
    prefix="/reader",
    tags=["reader"],
)


@router.get("/pdf")
async def get_pdf(
    url: str = Query(..., description="Public URL of a PDF"),
) -> Response:
    # Proxy: browsers block cross-origin PDF downloads (e.g. arXiv).
    try:
        pdf_bytes = await download_pdf(url)

    except PDFParserError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
    )
