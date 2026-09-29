from paper_digest.clients.claude import run_agent
from paper_digest.analyser.schemas import PaperAnalyzerResponse


PAPER_ANALYZER_PROMPT = """
You are the Paper Analyzer for Auto Learning.

You receive the extracted text of an AI or Machine Learning research paper.

Your job is ONLY to understand the paper itself.

Identify:

1. The main novel contribution introduced by the paper.

2. The direct technical concepts required to understand that contribution.

IMPORTANT:

Only identify concepts that are close to the paper's novel contribution.

Do NOT recursively decompose concepts into mathematical or foundational
prerequisites.

For example, if understanding the contribution requires Self-Attention,
return Self-Attention.

Do NOT expand Self-Attention into vectors, matrix multiplication,
exponentials, algebra, etc.

That decomposition belongs to another agent.

Do not include concepts merely because they are mentioned in the paper.
"""


async def analyze_paper_content(
    paper_text: str,
) -> PaperAnalyzerResponse:

    return await run_agent(
        prompt=f"""
Analyze the following research paper:

<PAPER>
{paper_text}
</PAPER>
""",
        system_prompt=PAPER_ANALYZER_PROMPT,
        response_model=PaperAnalyzerResponse,
    )