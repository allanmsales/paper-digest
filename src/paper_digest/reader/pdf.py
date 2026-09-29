import httpx
import pymupdf


class PDFParserError(Exception):
    pass


async def download_pdf(paper_url: str) -> bytes:
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
        ) as client:
            response = await client.get(paper_url)
            response.raise_for_status()

    except httpx.HTTPError as exc:
        raise PDFParserError(
            f"Failed to download PDF: {exc}"
        ) from exc

    pdf_bytes = response.content

    if not pdf_bytes.startswith(b"%PDF"):
        raise PDFParserError(
            "The provided URL did not return a valid PDF."
        )

    return pdf_bytes


def extract_pdf_text(pdf_bytes: bytes) -> str:
    try:
        document = pymupdf.open(
            stream=pdf_bytes,
            filetype="pdf",
        )

        pages: list[str] = []

        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text")

            if text.strip():
                pages.append(
                    f"\n--- PAGE {page_number} ---\n{text}"
                )
        document.close()

    except Exception as exc:
        raise PDFParserError(
            f"Failed to parse PDF: {exc}"
        ) from exc

    if not pages:
        raise PDFParserError(
            "No text could be extracted from the PDF."
        )

    return "\n".join(pages)


async def parse_pdf_from_url(paper_url: str) -> str:
    pdf_bytes = await download_pdf(paper_url)

    return extract_pdf_text(pdf_bytes)