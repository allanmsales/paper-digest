from paper_digest.analyser.agent import analyze_paper_content
from paper_digest.reader.pdf import parse_pdf_from_url
from paper_digest.splitter.agent import split_subjects
from paper_digest.splitter.schemas import PaperAnalysisResponse


async def analyze_paper(
    paper_url: str,
) -> PaperAnalysisResponse:

    # Download and parse PDF locally
    paper_text = await parse_pdf_from_url(paper_url)

    return await analyze_text(paper_text)


async def analyze_text(
    paper_text: str,
) -> PaperAnalysisResponse:

    # 1. Find paper contribution + direct concepts
    analysis = await analyze_paper_content(paper_text)

    # 2. Recursively expand prerequisites
    prerequisites = await split_subjects(analysis)

    # 3. Combine both agent results
    return PaperAnalysisResponse(
        new_subject=analysis.new_subject,
        direct_subjects=analysis.direct_subjects,
        subjects=prerequisites.subjects,
    )