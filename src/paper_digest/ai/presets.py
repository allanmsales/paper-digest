from paper_digest.ai.schemas import Preset


PRESETS = [
    Preset(
        id="anthropic",
        label="Anthropic (Claude)",
        provider="anthropic",
        fast_model="claude-haiku-4-5",
        smart_model="claude-sonnet-5-5",
        help="Best results and the cheapest lookups (prompt caching). Key from console.anthropic.com.",
    ),
    Preset(
        id="openai",
        label="OpenAI",
        provider="openai",
        help="Key from platform.openai.com. Click “Load models” and pick a small (fast) and a strong (smart) model.",
    ),
    Preset(
        id="compatible",
        label="Other OpenAI-compatible API",
        provider="compatible",
        help="Any server with /v1/chat/completions (Ollama, vLLM, OpenRouter…). Enter its base URL, ending in /v1.",
    ),
]
