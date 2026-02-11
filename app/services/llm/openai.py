import logging

from openai import AsyncOpenAI

from app.config import settings
from app.services.llm.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    async def generate(self, system_prompt: str, user_message: str) -> LLMResponse:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=settings.llm_temperature,
            )
            choice = response.choices[0].message
            usage = response.usage

            return LLMResponse(
                content=choice.content or "",
                model=response.model,
                tokens_used=usage.total_tokens if usage else 0,
            )
        except Exception:
            logger.exception("OpenAI API error")
            raise
