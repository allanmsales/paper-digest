import json

from paper_digest.agents.runner import run_agent
from paper_digest.schemas.paper import (
    PaperAnalyzerResponse,
    SubjectSplitterResponse,
)


SUBJECT_SPLITTER_PROMPT = """
You are the Subject Splitter for Auto Learning.

You receive:

- the main novel subject of a research paper
- the direct concepts required to understand it

Your responsibility is to recursively decompose those concepts into
their minimum sufficient prerequisites.

For each concept ask:

"What must someone already understand before they can understand
this concept?"

Continue recursively until reaching foundational concepts.

IMPORTANT:

Preserve intermediate concepts.

Do NOT jump directly from a high-level concept to basic mathematics.

For example:

Self-Attention
→ Scaled Dot-Product Attention
→ Dot Product
→ Vectors
→ Multiplication and Summation

is preferable to:

Self-Attention
→ Basic Algebra

Only include knowledge that contributes to understanding the target.

Avoid broad subjects such as:

- Algebra
- Linear Algebra
- Probability
- Trigonometry

Instead identify only the specific parts actually required, such as:

- Summation notation
- Matrix multiplication
- Exponential function
- Probability distributions
- Sine and cosine

Represent every concept as a dependency relationship.

Foundation concepts should have an empty requires list.
"""


async def split_subjects(
    analysis: PaperAnalyzerResponse,
) -> SubjectSplitterResponse:

    input_data = {
        "new_subject": analysis.new_subject,
        "direct_subjects": analysis.direct_subjects,
    }

    return await run_agent(
        prompt=f"""
Create the prerequisite dependency graph for:

{json.dumps(input_data, indent=2)}
""",
        system_prompt=SUBJECT_SPLITTER_PROMPT,
        response_model=SubjectSplitterResponse,
    )