import asyncio

from paper_digest.clients.claude import ask_claude_once
from paper_digest.core.config import settings
from paper_digest.podcast.schemas import Script
from paper_digest.podcast.store import load_script, save_script
from paper_digest.reader.store import get_paper


SYSTEM_PROMPT = """
You write a podcast episode that helps a listener learn one AI/ML research
paper, shown below. It is an interview between a curious host and the
paper's author.

The listener is smart but does NOT know this field, and is only listening,
not reading. Always:

- The host asks the 8-12 questions that matter most for understanding this
  paper: the problem, why it is hard, the key idea, how it works, what the
  results show, the limits, and why it matters. Build up in that order.
- The author answers in everyday words, as if talking to a friend. Short,
  complete sentences. One idea per sentence. Use a concrete example or
  analogy when an idea is abstract.
- Never copy the paper's technical wording. If a key term must appear,
  name it once and explain it in the same sentence.
- No math notation, symbols, tables, citations or URLs: everything is
  spoken aloud. Say numbers the way a person would say them.
- Stay on this paper; never branch into topics it does not need.
- Host turns: 1-2 sentences. Author turns: 2-5 sentences.
- The host opens with a one-sentence welcome naming the topic, and closes
  with a one-sentence thanks. About 1,300-1,600 words in total.
- Plain text only, no markdown, no stage directions.

The full paper follows. Page markers look like "--- PAGE n ---".
"""

TASK = "Write the episode. title: a short, plain episode title."

_scripts: dict[str, asyncio.Task[Script]] = {}


async def podcast_script(paper_id: str) -> Script:
    # One generation per paper, even with concurrent requests.
    if paper_id not in _scripts:
        _scripts[paper_id] = asyncio.create_task(_load_or_create_script(paper_id))
    try:
        return await asyncio.shield(_scripts[paper_id])
    except Exception:
        # Let the next request retry instead of caching the failure.
        _scripts.pop(paper_id, None)
        raise


async def _load_or_create_script(paper_id: str) -> Script:
    script = load_script(paper_id)
    if script is None:
        paper = get_paper(paper_id)
        if paper is None:
            raise LookupError(f"Unknown paper {paper_id}")
        script = await ask_claude_once(
            model=settings.summary_model,
            system=SYSTEM_PROMPT + f"\n<PAPER>\n{paper.text}\n</PAPER>",
            prompt=TASK,
            response_model=Script,
            max_tokens=8000,
        )
        save_script(paper_id, script)
    return script
