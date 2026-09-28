from paper_digest.agents.paper_analyser import analyze_paper_content
from paper_digest.agents.subject_splitter import split_subjects
from paper_digest.schemas.paper import PaperAnalysisResponse
from paper_digest.services.pdf_parser import parse_pdf_from_url


async def analyze_paper(
    paper_url: str,
) -> PaperAnalysisResponse:

    # 1. Download and parse PDF locally
    paper_text = await parse_pdf_from_url(paper_url)

    # 2. Find paper contribution + direct concepts
    analysis = await analyze_paper_content(paper_text)

    # 3. Recursively expand prerequisites
    prerequisites = await split_subjects(analysis)

    # 4. Combine both agent results
    return PaperAnalysisResponse(
        new_subject=analysis.new_subject,
        direct_subjects=analysis.direct_subjects,
        subjects=prerequisites.subjects,
    )