"""Provider-agnostic LLM calls: Anthropic, OpenAI, or any OpenAI-compatible
API (e.g. a hosted Qwen). Domains ask for a tier, never a model name:

- "fast": many small calls (lookups, checks, links).
- "smart": one-off writing that needs care (summary, feed, podcast, video).

The active provider is set with `configure()` (the `ai` domain does it at
startup and whenever an admin saves new settings).
"""

import json
import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, TypeVar

import anthropic
import openai
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError


T = TypeVar("T", bound=BaseModel)

Tier = Literal["fast", "smart"]
Provider = Literal["anthropic", "openai", "compatible"]
AuthHeader = Literal["bearer", "x-api-key"]

logger = logging.getLogger("uvicorn.error")

# Long outputs (a whole feed, a video storyboard) can take minutes.
TIMEOUT_SECONDS = 600


class LlmNotConfigured(RuntimeError):
    """No AI provider is set up yet."""


@dataclass(frozen=True)
class LlmConfig:
    provider: Provider
    api_key: str
    fast_model: str
    smart_model: str
    base_url: str | None = None
    auth_header: AuthHeader = "bearer"

    def model(self, tier: Tier) -> str:
        return self.fast_model if tier == "fast" else self.smart_model


_config: LlmConfig | None = None
_anthropic: AsyncAnthropic | None = None
_openai: AsyncOpenAI | None = None


def configure(config: LlmConfig | None) -> None:
    global _config, _anthropic, _openai
    _config, _anthropic, _openai = config, None, None


def current_config() -> LlmConfig | None:
    return _config


def _require_config() -> LlmConfig:
    if _config is None:
        raise LlmNotConfigured(
            "No AI provider is set up. An admin can add one in Admin → AI provider."
        )
    return _config


def anthropic_client(config: LlmConfig) -> AsyncAnthropic:
    return AsyncAnthropic(api_key=config.api_key, timeout=TIMEOUT_SECONDS)


def openai_client(config: LlmConfig) -> AsyncOpenAI:
    headers = {"x-api-key": config.api_key} if config.auth_header == "x-api-key" else None
    return AsyncOpenAI(
        api_key=config.api_key or "not-needed",
        base_url=config.base_url or None,
        default_headers=headers,
        timeout=TIMEOUT_SECONDS,
    )


def _clients(config: LlmConfig) -> AsyncAnthropic | AsyncOpenAI:
    """The client for `config`: shared for the active config, fresh otherwise
    (e.g. a connection test of unsaved settings)."""
    global _anthropic, _openai
    if config is not _config:
        return anthropic_client(config) if config.provider == "anthropic" else openai_client(config)
    if config.provider == "anthropic":
        if _anthropic is None:
            _anthropic = anthropic_client(config)
        return _anthropic
    if _openai is None:
        _openai = openai_client(config)
    return _openai


# --- Shared helpers ----------------------------------------------------------


def _closed_schema(schema: dict) -> dict:
    """Sets additionalProperties: false on every object, as structured
    outputs require."""
    if schema.get("type") == "object":
        schema["additionalProperties"] = False
    for value in schema.values():
        if isinstance(value, dict):
            _closed_schema(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _closed_schema(item)
    return schema


_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


def _extract_json(text: str) -> str:
    """The JSON object in a reply that may carry reasoning or code fences."""
    text = _THINK.sub("", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end < start:
        raise ValueError("The reply contained no JSON object.")
    return text[start : end + 1]


# --- Anthropic -----------------------------------------------------------------

# Models that accept server-side refusal fallbacks ("default" routing).
_FALLBACK_MODELS = {"claude-fable-5-1", "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5"}


def _log_anthropic_usage(usage) -> None:
    logger.info(
        "llm usage (anthropic): input=%s cache_write=%s cache_read=%s output=%s",
        usage.input_tokens,
        usage.cache_creation_input_tokens,
        usage.cache_read_input_tokens,
        usage.output_tokens,
    )


def _tools(response_models: Sequence[type[BaseModel]]) -> list[dict]:
    return [
        {
            "name": model.__name__,
            "description": model.__doc__ or model.__name__,
            "input_schema": model.model_json_schema(),
        }
        for model in sorted(response_models, key=lambda m: m.__name__)
    ]


def _cached_system(system: str, document: str) -> list[dict]:
    return [
        {"type": "text", "text": system},
        {
            "type": "text",
            "text": document,
            "cache_control": {"type": "ephemeral"},
        },
    ]


async def _anthropic_cached(
    config: LlmConfig,
    system: str,
    document: str,
    prompt: str,
    response_model: type[T],
    response_models: Sequence[type[BaseModel]],
    max_tokens: int,
) -> T:
    # Every answer format is declared as a tool (same list on every call
    # keeps the cache shared) and the wanted one is forced: tool_choice is
    # not part of the cached prefix.
    response = await _clients(config).messages.create(
        model=config.fast_model,
        max_tokens=max_tokens,
        tools=_tools(response_models),
        tool_choice={"type": "tool", "name": response_model.__name__},
        system=_cached_system(system, document),
        messages=[{"role": "user", "content": prompt}],
    )
    _log_anthropic_usage(response.usage)

    tool_use = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_use is None:
        raise RuntimeError(f"No structured output (stop_reason={response.stop_reason}).")
    return response_model.model_validate(tool_use.input)


async def _anthropic_once(
    config: LlmConfig,
    model: str,
    system: str,
    prompt: str,
    response_model: type[T],
    max_tokens: int,
) -> T:
    output_config: dict = {
        "format": {
            "type": "json_schema",
            "schema": _closed_schema(response_model.model_json_schema()),
        },
    }
    if "haiku" not in model:
        output_config["effort"] = "low"

    params = dict(
        model=model,
        max_tokens=max_tokens,
        output_config=output_config,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    # Streamed so large outputs don't hit HTTP timeouts.
    client = _clients(config)
    if model in _FALLBACK_MODELS:
        stream = client.beta.messages.stream(
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            **params,
        )
    else:
        stream = client.messages.stream(**params)
    async with stream as events:
        response = await events.get_final_message()
    _log_anthropic_usage(response.usage)

    if response.stop_reason == "refusal":
        raise RuntimeError("The model declined this request.")
    text = next((b.text for b in response.content if b.type == "text"), None)
    if text is None or response.stop_reason == "max_tokens":
        raise RuntimeError(
            f"No complete structured output (stop_reason={response.stop_reason})."
        )
    return response_model.model_validate_json(text)


# --- OpenAI and OpenAI-compatible ---------------------------------------------


def _log_openai_usage(config: LlmConfig, usage) -> None:
    if usage is None:
        return
    details = getattr(usage, "prompt_tokens_details", None)
    logger.info(
        "llm usage (%s): input=%s cache_read=%s output=%s",
        config.provider,
        usage.prompt_tokens,
        getattr(details, "cached_tokens", None),
        usage.completion_tokens,
    )


async def _openai_json(
    config: LlmConfig,
    model: str,
    messages: list[dict],
    response_model: type[T],
    max_tokens: int,
) -> T:
    """Chat completion constrained to `response_model`, with one repair retry."""

    schema = _closed_schema(response_model.model_json_schema())
    if config.provider == "compatible":
        # Not every server enforces response_format; spell the schema out too.
        messages = [
            *messages[:-1],
            {
                "role": messages[-1]["role"],
                "content": messages[-1]["content"]
                + "\n\nReply with only a JSON object (no other text) that matches"
                f" this JSON schema:\n{json.dumps(schema)}",
            },
        ]

    params: dict = {"model": model, "messages": messages}
    if config.provider == "openai":
        params["max_completion_tokens"] = max_tokens
    else:
        params["max_tokens"] = max_tokens
    response_format = {
        "type": "json_schema",
        "json_schema": {"name": response_model.__name__, "schema": schema, "strict": False},
    }

    client = _clients(config)
    try:
        response = await client.chat.completions.create(
            **params, response_format=response_format
        )
    except openai.BadRequestError as exc:
        if config.provider != "compatible":
            raise
        # Some servers reject json_schema: rely on the instructions instead.
        logger.info("response_format rejected (%s); retrying without it", exc)
        response = await client.chat.completions.create(**params)
    _log_openai_usage(config, response.usage)

    choice = response.choices[0]
    if choice.finish_reason == "length":
        raise RuntimeError("The answer was cut off (max tokens). Try a larger model.")
    text = choice.message.content or ""

    try:
        return response_model.model_validate_json(_extract_json(text))
    except (ValueError, ValidationError) as exc:
        problem = str(exc)[:500]
        logger.info("invalid structured output, asking for a repair: %s", problem)

    repair = await client.chat.completions.create(
        **{
            **params,
            "messages": [
                *params["messages"],
                {"role": "assistant", "content": text},
                {
                    "role": "user",
                    "content": "That reply did not match the JSON schema"
                    f" ({problem}). Reply again with only the corrected JSON object.",
                },
            ],
        }
    )
    _log_openai_usage(config, repair.usage)
    return response_model.model_validate_json(
        _extract_json(repair.choices[0].message.content or "")
    )


# --- Public API ----------------------------------------------------------------


async def ask_cached(
    system: str,
    document: str,
    prompt: str,
    response_model: type[T],
    response_models: Sequence[type[BaseModel]],
    max_tokens: int = 1024,
) -> T:
    """A fast-tier call about a large `document` (the paper), cached where
    the provider allows it.

    The prefix (system + document, and on Anthropic the tools built from
    `response_models`) must be identical across calls; put anything that
    varies in `prompt`. OpenAI caches long identical prefixes on its own.
    """
    config = _require_config()
    if config.provider == "anthropic":
        return await _anthropic_cached(
            config, system, document, prompt, response_model, response_models, max_tokens
        )
    return await _openai_json(
        config,
        config.fast_model,
        [
            {"role": "system", "content": f"{system}\n\n{document}"},
            {"role": "user", "content": prompt},
        ],
        response_model,
        max_tokens,
    )


async def warm(
    system: str,
    document: str,
    response_models: Sequence[type[BaseModel]],
) -> None:
    """Pre-writes the `ask_cached` prefix to the prompt cache (Anthropic only;
    other providers cache on the first real call, or not at all)."""
    config = _require_config()
    if config.provider != "anthropic":
        return
    # tool_choice auto: max_tokens=0 rejects a forced tool, and tool_choice
    # is not part of the cached prefix.
    response = await _clients(config).messages.create(
        model=config.fast_model,
        max_tokens=0,
        tools=_tools(response_models),
        tool_choice={"type": "auto"},
        system=_cached_system(system, document),
        messages=[{"role": "user", "content": "warm-up"}],
    )
    _log_anthropic_usage(response.usage)


async def ask_once(
    tier: Tier,
    system: str,
    prompt: str,
    response_model: type[T],
    max_tokens: int = 4096,
) -> T:
    """One uncached structured-output call."""
    return await _ask_once(_require_config(), tier, system, prompt, response_model, max_tokens)


async def _ask_once(
    config: LlmConfig,
    tier: Tier,
    system: str,
    prompt: str,
    response_model: type[T],
    max_tokens: int,
) -> T:
    model = config.model(tier)
    if config.provider == "anthropic":
        return await _anthropic_once(config, model, system, prompt, response_model, max_tokens)
    return await _openai_json(
        config,
        model,
        [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        response_model,
        max_tokens,
    )


class _Ping(BaseModel):
    """Connection test."""

    reply: str


async def test_connection(config: LlmConfig, tier: Tier) -> str:
    """Runs a tiny structured call with `config` (which may be unsaved)."""
    result = await _ask_once(
        config,
        tier,
        system="You are a connection test.",
        prompt='Set reply to "ok".',
        response_model=_Ping,
        # Room for models that think before answering.
        max_tokens=1000,
    )
    return result.reply


def describe_error(exc: Exception, config: LlmConfig) -> str:
    """A plain explanation of a provider error, for the admin form."""
    if isinstance(exc, openai.APIConnectionError | anthropic.APIConnectionError):
        return "Can't reach the server. Check the base URL and your network."
    status = getattr(exc, "status_code", None)
    if status in (401, 403):
        return "The key was rejected. Check that it's current and complete."
    if status == 404:
        if config.provider == "compatible":
            return (
                "Not found. Check the base URL (it usually ends in /v1) and the model"
                " name. Some servers also answer 404 to an unknown key."
            )
        return "Not found. Check the model name."
    return str(exc)


async def list_models(config: LlmConfig) -> list[str]:
    """Model ids the provider offers, for the admin form."""
    if config.provider == "anthropic":
        page = await anthropic_client(config).models.list(limit=100)
        return [model.id for model in page.data]
    page = await openai_client(config).models.list()
    return sorted(model.id for model in page.data)
