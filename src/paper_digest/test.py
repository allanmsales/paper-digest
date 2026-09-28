import asyncio

from paper_digest.agents.runner import run_orchestrator


TEST_PROMPT = """
Analyze this hypothetical research paper.

The paper proposes a new architecture called Sparse Gated Attention.

Instead of allowing every token to attend to every other token,
the model learns a gating function that selects a small subset of
relevant tokens before computing attention.

The paper discusses:
- self-attention
- query, key and value vectors
- softmax
- top-k selection
- gating functions
- sparse computation
- matrix multiplication

The main claimed contribution is reducing attention computation
while maintaining model quality.
"""


async def main():
    result = await run_orchestrator(TEST_PROMPT)

    print("\n=== FINAL RESULT ===\n")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())