import asyncio
import time

from paper_digest.clients.claude import ask_claude, ask_claude_once, warm_claude
from paper_digest.core.config import settings
from paper_digest.explainer.store import (
    add_signals,
    load_summary,
    save_check,
    save_lookup,
    save_summary,
)
from paper_digest.reader.store import paper_id, save_paper
from paper_digest.explainer.schemas import (
    AnalogyResponse,
    AskRequest,
    AskResponse,
    CheckedIdea,
    CheckGrades,
    CheckResponse,
    ExplainRequest,
    ExplainResponse,
    SummaryResponse,
)


# Shared by every explainer task so they all hit the same prompt cache
# (system + paper). Task-specific instructions go after the paper.
SYSTEM_PROMPT = """
You help a person learn one AI/ML research paper, shown below.

The reader has limited attention. Every extra word costs them energy they
need to finish the paper. Always:

- Write for a smart reader who does NOT know this field. Do not reuse the
  paper's technical wording. Say what it means in everyday words instead.
- If a key term of the paper must appear, name it once and explain it in
  the same sentence (e.g. "a new metric, called X, that measures ...").
- Short, complete sentences. One idea per sentence.
- No introductions, no restating the question, no background history.
- Stay close to this paper; never branch into topics it does not need.
- Plain text only, no markdown.

The full paper follows. Page markers look like "--- PAGE n ---".
"""

TERM_TASK = """
Task: the reader selected a term they do not understand.
- meaning: what it means IN THIS PAPER, one or two sentences, max 35 words.
- points: empty list.
"""

PASSAGE_TASK = """
Task: the reader selected a passage they find hard.
- points: 2-3 bullets saying what the passage says, max 15 words each.
- meaning: null.
"""

COMMON_EXPLAIN_RULES = """
- defined_at: only a location like "Section 3.2, page 4". No quotes. Null if
  the paper never explains it.
- learn_first: at most 2 specific concepts (never broad fields like
  "Linear Algebra"). Empty list if they can understand it as is.
- If there is a READER_GUESS: guess_feedback is ONE sentence saying if they
  are right and what to fix. Otherwise null. Do not mention the guess
  anywhere else.
"""

SUMMARY_TASK = """
Task: summarize the whole paper for someone about to read it.
problem, idea, result: one or two plain sentences each (max 35 words).

The reader is a curious 15-year-old. Rules:
- Never copy phrases from the paper. Say what they mean.
- Never name specific models, datasets, benchmarks or experiment details.
- At most one technical term in total, explained in the same sentence.
- Before answering, reread each sentence: if any word would confuse a
  15-year-old, rewrite it.

sections: the Abstract first, then the paper's main numbered sections in
order (skip references and appendices; merge tiny ones; max 7). For each,
2-4 key_ideas someone must grasp from it, same plain style. They are used
to check the reader's own summary of that section.

Style example (from a different paper):
- problem: "Chatbots often sound confident even when they are wrong, and
  users cannot tell the difference."
- idea: "The authors train the model to say how sure it is, and check if
  that confidence matches how often it is actually right."
- result: "The model's confidence became much more honest, so users could
  spot the answers worth double-checking."
"""

ANALOGY_TASK = """
Task: explain the SUBJECT with an everyday-life analogy a 12-year-old gets.
- analogy: 2-3 short sentences.
- mapping: 2-4 links from elements of the analogy to the paper's real terms,
  so the reader can map the analogy back to the paper.
"""

CHECK_TASK = """
Task: the reader wrote, in their own words, what they understood from one
SECTION of the paper. Grade it against each KEY_IDEA of that section.
- covered: true if the answer expresses the idea in any words. Paraphrases,
  simpler words and analogies count. Be fair, not strict.
- reread_at: only for ideas not covered: the section and page where the
  paper explains it, e.g. "Section 3, page 5". Null if covered.
- Return one grade per key idea, in order.
"""

ASK_TASK = """
Task: the reader has a question about one point of the paper (the ANCHOR).
Answer their last question in the CONVERSATION.
- answer: 2-3 short sentences, max 45 words. Answer only what they asked.
- Write for a curious 15-year-old: never copy the paper's phrases, never
  use terms the reader did not use. If they ask what a term means, say it
  in everyday words.
- If the question drifts away from this paper, answer in one sentence and
  bring them back to how it matters for the paper.
- reread_at: the section and page that best explains it, or null.
"""

# Selections longer than this are treated as passages, not terms.
TERM_MAX_WORDS = 12

# The prompt cache lives 5 minutes (refreshed on each hit); skip re-warming
# a paper warmed more recently than this.
WARM_INTERVAL_SECONDS = 240

# In-memory answer caches, keyed by paper hash. Cleared on API restart.
_explanations: dict[tuple[str, str], ExplainResponse] = {}
# Tasks, not results: concurrent requests for the same paper (warm-up and
# the Summary card) share one Sonnet call.
_summaries: dict[str, asyncio.Task[SummaryResponse]] = {}
_analogies: dict[tuple[str, str], AnalogyResponse] = {}
_warmed_at: dict[str, float] = {}


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


# Every explainer answer format; declared together on each call so all
# tasks share one prompt cache.
RESPONSE_MODELS = (
    AnalogyResponse,
    AskResponse,
    CheckGrades,
    ExplainResponse,
    SummaryResponse,
)


async def _ask(paper_text: str, prompt: str, response_model):
    return await ask_claude(
        system=SYSTEM_PROMPT,
        document=f"<PAPER>\n{paper_text}\n</PAPER>",
        prompt=prompt,
        response_model=response_model,
        response_models=RESPONSE_MODELS,
    )


async def explain_selection(
    request: ExplainRequest,
    user_id: int,
) -> ExplainResponse:

    cache_key = (paper_id(request.paper_text), _normalize(request.selection))
    add_signals(cache_key[0], user_id, "lookup", [request.selection])
    if not request.guess and cache_key in _explanations:
        answer = _explanations[cache_key]
        save_lookup(user_id, cache_key[0], request.selection, None, answer)
        return answer

    is_term = len(request.selection.split()) <= TERM_MAX_WORDS
    page_hint = f"The reader is on page {request.page}.\n" if request.page else ""
    guess_block = (
        f"<READER_GUESS>\n{request.guess}\n</READER_GUESS>\n"
        if request.guess
        else ""
    )

    answer = await _ask(
        request.paper_text,
        (TERM_TASK if is_term else PASSAGE_TASK)
        + COMMON_EXPLAIN_RULES
        + f"\n{page_hint}<SELECTION>\n{request.selection}\n</SELECTION>\n"
        + guess_block,
        ExplainResponse,
    )

    if not request.guess:
        _explanations[cache_key] = answer

    save_lookup(user_id, cache_key[0], request.selection, request.guess, answer)
    return answer


async def summarize_paper(paper_text: str) -> SummaryResponse:
    # Runs once per paper on the stronger model: plain rewriting is where
    # the cheaper model keeps slipping back into the paper's jargon.
    key = paper_id(paper_text)
    if key not in _summaries:
        _summaries[key] = asyncio.create_task(_load_or_create_summary(key, paper_text))
    try:
        return await asyncio.shield(_summaries[key])
    except Exception:
        # Let the next request retry instead of caching the failure.
        _summaries.pop(key, None)
        raise


async def _load_or_create_summary(key: str, paper_text: str) -> SummaryResponse:
    # Saved, so sections and key ideas stay the same across restarts.
    summary = load_summary(key)
    if summary is None:
        summary = await ask_claude_once(
            model=settings.summary_model,
            system=SYSTEM_PROMPT + f"\n<PAPER>\n{paper_text}\n</PAPER>",
            prompt=SUMMARY_TASK,
            response_model=SummaryResponse,
        )
        save_summary(key, summary)
    return summary


async def explain_by_analogy(paper_text: str, subject: str) -> AnalogyResponse:
    cache_key = (paper_id(paper_text), _normalize(subject))
    if cache_key not in _analogies:
        _analogies[cache_key] = await _ask(
            paper_text,
            ANALOGY_TASK + f"\n<SUBJECT>\n{subject}\n</SUBJECT>\n",
            AnalogyResponse,
        )
    return _analogies[cache_key]


async def check_understanding(
    paper_text: str,
    section_index: int,
    answer: str,
    user_id: int,
) -> CheckResponse:
    sections = (await summarize_paper(paper_text)).sections
    if section_index >= len(sections):
        raise ValueError(f"The paper has {len(sections)} sections.")
    section = sections[section_index]
    key_ideas = section.key_ideas
    listed = "\n".join(f"{i}. {idea}" for i, idea in enumerate(key_ideas))

    result = await _ask(
        paper_text,
        CHECK_TASK
        + f"\n<SECTION>\n{section.title} (page {section.page})\n</SECTION>\n"
        + f"\n<KEY_IDEAS>\n{listed}\n</KEY_IDEAS>\n"
        + f"\n<READER_ANSWER>\n{answer}\n</READER_ANSWER>\n",
        CheckGrades,
    )

    grades = {grade.index: grade for grade in result.grades}
    ideas = [
        CheckedIdea(
            idea=idea,
            covered=bool(grades.get(i) and grades[i].covered),
            reread_at=None if grades.get(i) and grades[i].covered
            else (grades[i].reread_at if i in grades else None),
        )
        for i, idea in enumerate(key_ideas)
    ]

    covered = sum(idea.covered for idea in ideas)
    if covered == len(ideas):
        level = "got_it"
    elif covered * 2 >= len(ideas):
        level = "partly"
    else:
        level = "not_yet"

    key = paper_id(paper_text)
    add_signals(
        key,
        user_id,
        "missed_idea",
        [idea.idea for idea in ideas if not idea.covered],
    )

    response = CheckResponse(level=level, ideas=ideas)
    save_check(user_id, key, section_index, answer, response)
    return response


async def answer_question(request: AskRequest, user_id: int) -> AskResponse:
    add_signals(
        paper_id(request.paper_text),
        user_id,
        "question",
        [f"{request.messages[-1].content} (about: {request.anchor})"],
    )

    speaker = {"reader": "Reader", "assistant": "You"}
    conversation = "\n".join(
        f"{speaker[message.role]}: {message.content}" for message in request.messages
    )

    return await _ask(
        request.paper_text,
        ASK_TASK
        + f"\n<ANCHOR>\n{request.anchor}\n</ANCHOR>\n"
        + f"\n<CONVERSATION>\n{conversation}\n</CONVERSATION>\n",
        AskResponse,
    )


def register_paper(paper_text: str, source: str | None) -> str:
    return save_paper(paper_text, source)


async def warm_paper(paper_text: str) -> None:
    """Writes the paper to the prompt cache and prepares its summary,
    so the first lookup is fast and the Summary button is instant."""
    key = paper_id(paper_text)
    now = time.monotonic()
    if now - _warmed_at.get(key, float("-inf")) < WARM_INTERVAL_SECONDS:
        return
    _warmed_at[key] = now

    await asyncio.gather(
        warm_claude(
            system=SYSTEM_PROMPT,
            document=f"<PAPER>\n{paper_text}\n</PAPER>",
            response_models=RESPONSE_MODELS,
        ),
        summarize_paper(paper_text),
    )
