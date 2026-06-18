from __future__ import annotations

import os
from typing import TypeVar

from pydantic import BaseModel
from pydantic_ai import Agent

from caresync.config import Settings

T = TypeVar("T", bound=BaseModel)

# The safety crux: the model transcribes what it hears and never sanitizes it -- a
# wrong value must survive extraction so the carer is asked about it.
_INSTRUCTIONS = """\
You transcribe a German elderly-care worker's spoken shift notes into structured \
fields. Fill in the resident's name, any vital signs mentioned (blood pressure, \
temperature, pulse, oxygen saturation), and any free-text note. Leave a field null \
if it was not mentioned.

Record exactly what was said. Do not clamp, round, convert units, or "correct" a \
value even if it seems physiologically impossible -- transcribe the number you hear. \
A human carer reviews and fixes implausible readings afterwards.
"""


class Extractor:
    """A PydanticAI-backed extractor, built from settings.
    """
    def __init__(self, settings: Settings) -> None:
        if not settings.llm_model:
            raise RuntimeError(
                "LLM_MODEL is not set. Configure it (and the matching "
                "<PROVIDER>_API_KEY) in the environment or .env before extracting."
            )

        if settings.llm_base_url:
            from pydantic_ai.models.openai import OpenAIChatModel
            from pydantic_ai.providers.openai import OpenAIProvider

            model = OpenAIChatModel(
                settings.llm_model.removeprefix("openai:"),
                provider=OpenAIProvider(
                    base_url=settings.llm_base_url,
                    # Local endpoints usually ignore the key but the client requires one.
                    api_key=os.environ.get("OPENAI_API_KEY", "not-needed"),
                ),
            )
        else:
            model = settings.llm_model

        self._agent = Agent(model, instructions=_INSTRUCTIONS)

    def extract(self, transcript: str, output_type: type[T]) -> T:
        """Run the model and return its structured output of the requested type."""
        return self._agent.run_sync(transcript, output_type=output_type).output
