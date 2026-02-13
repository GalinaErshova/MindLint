import logging

from anthropic import AsyncAnthropic

from app.config import settings
from app.services.llm.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    async def generate(self, system_prompt: str, user_message: str) -> LLMResponse:
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message},
                ],
                temperature=settings.llm_temperature,
            )
            content = response.content[0].text if response.content else ""
            tokens_used = (
                response.usage.input_tokens + response.usage.output_tokens
            )

            return LLMResponse(
                content=content,
                model=response.model,
                tokens_used=tokens_used,
            )
        except Exception:
            logger.exception("Anthropic API error")
            raise

    async def generate_with_history(
        self, system_prompt: str, messages: list[dict[str, str]]
    ) -> LLMResponse:
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=system_prompt,
                messages=messages,
                temperature=settings.llm_temperature,
            )
            content = response.content[0].text if response.content else ""
            tokens_used = (
                response.usage.input_tokens + response.usage.output_tokens
            )

            return LLMResponse(
                content=content,
                model=response.model,
                tokens_used=tokens_used,
            )
        except Exception:
            logger.exception("Anthropic API error")
            raise
