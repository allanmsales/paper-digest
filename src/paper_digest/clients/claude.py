import logging
from collections.abc import Sequence
from typing import TypeVar

from anthropic import AsyncAnthropic
from pydantic import BaseModel

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
)

from paper_digest.core.config import settings


T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger("uvicorn.error")


async def run_agent(
    prompt: str,
    system_prompt: str,
    response_model: type[T],
) -> T:

    options = ClaudeAgentOptions(
        model=settings.claude_model,
        system_prompt=system_prompt,
        output_format={
            "type": "json_schema",
            "schema": response_model.model_json_schema(),
        },
    )

    async with ClaudeSDKClient(options=options) as client:

        await client.query(prompt)

        async for message in client.receive_response():

            if isinstance(message, ResultMessage):

                if message.is_error:
                    raise RuntimeError(
                        message.result or "Claude returned an error"
                    )

                if message.structured_output is None:
                    raise RuntimeError(
                        f"Claude returned no structured output. "
                        f"Raw result: {message.result}"
                    )

                return response_model.model_validate(
                    message.structured_output
                )

    raise RuntimeError("Claude returned no final result")

_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


def _log_usage(usage) -> None:
    logger.info(
        "claude usage: input=%s cache_write=%s cache_read=%s output=%s",
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


async def ask_claude(
    system: str,
    document: str,
    prompt: str,
    response_model: type[T],
    response_models: Sequence[type[BaseModel]],
    max_tokens: int = 1024,
) -> T:
    """Single Messages API call with `document` prompt-cached.

    The cached prefix is tools + system + document, so it must be identical
    across calls; put anything that varies in `prompt`. Every model in
    `response_models` is declared as a tool (same list on every call keeps
    the cache shared) and `response_model`'s tool is forced, since
    `tool_choice` can change without invalidating the cache.
    """

    response = await _get_client().messages.create(
        model=settings.claude_model,
        max_tokens=max_tokens,
        tools=_tools(response_models),
        tool_choice={"type": "tool", "name": response_model.__name__},
        system=_cached_system(system, document),
        messages=[{"role": "user", "content": prompt}],
    )
    _log_usage(response.usage)

    tool_use = next(
        (block for block in response.content if block.type == "tool_use"),
        None,
    )
    if tool_use is None:
        raise RuntimeError(
            f"Claude returned no structured output (stop_reason={response.stop_reason})"
        )

    return response_model.model_validate(tool_use.input)


async def warm_claude(
    system: str,
    document: str,
    response_models: Sequence[type[BaseModel]],
) -> None:
    """Writes the `ask_claude` prefix to the prompt cache, generating nothing.

    Uses `tool_choice` auto because `max_tokens=0` rejects a forced tool;
    `tool_choice` is not part of the cached prefix.
    """

    response = await _get_client().messages.create(
        model=settings.claude_model,
        max_tokens=0,
        tools=_tools(response_models),
        tool_choice={"type": "auto"},
        system=_cached_system(system, document),
        messages=[{"role": "user", "content": "warm-up"}],
    )
    _log_usage(response.usage)


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


async def ask_claude_once(
    model: str,
    system: str,
    prompt: str,
    response_model: type[T],
    max_tokens: int = 4096,
    effort: str | None = "low",
    fallbacks: bool = True,
) -> T:
    """One uncached structured-output call, for one-off tasks.

    `effort` and server-side `fallbacks` are not supported on every model
    (e.g. Haiku 4.5): pass `effort=None, fallbacks=False` there.
    """

    output_config: dict = {
        "format": {
            "type": "json_schema",
            "schema": _closed_schema(response_model.model_json_schema()),
        },
    }
    if effort:
        output_config["effort"] = effort

    params = dict(
        model=model,
        max_tokens=max_tokens,
        output_config=output_config,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    # Streamed so large outputs (e.g. a whole feed) don't hit HTTP timeouts.
    client = _get_client()
    if fallbacks:
        stream = client.beta.messages.stream(
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            **params,
        )
    else:
        stream = client.messages.stream(**params)
    async with stream as events:
        response = await events.get_final_message()
    _log_usage(response.usage)

    if response.stop_reason == "refusal":
        raise RuntimeError("Claude declined this request.")

    text = next(
        (block.text for block in response.content if block.type == "text"),
        None,
    )
    if text is None or response.stop_reason == "max_tokens":
        raise RuntimeError(
            f"Claude returned no complete structured output (stop_reason={response.stop_reason})"
        )

    return response_model.model_validate_json(text)
