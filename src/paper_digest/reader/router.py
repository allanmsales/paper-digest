from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel

from paper_digest.reader.pdf import PDFParserError, download_pdf
from paper_digest.reader.store import list_library
from paper_digest.users.auth import current_user
from paper_digest.users.models import User


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


class LibraryItem(BaseModel):
    paper_id: str
    source: str | None
    last_opened: datetime


@router.get("/library", response_model=list[LibraryItem])
async def library(
    user: Annotated[User, Depends(current_user)],
) -> list[LibraryItem]:

    return [
        LibraryItem(paper_id=entry.paper_id, source=entry.source, last_opened=entry.last_opened)
        for entry in list_library(user.id)
    ]
