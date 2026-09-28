from typing import TypeVar

from pydantic import BaseModel

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
)

from paper_digest.config import settings


T = TypeVar("T", bound=BaseModel)


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