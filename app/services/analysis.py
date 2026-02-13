import logging
from pathlib import Path

from app.config import settings
from app.services.llm.base import LLMResponse
from app.services.llm.factory import LLMProviderFactory

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "system_prompt.txt"


class AnalysisService:
    def __init__(self) -> None:
        self._provider = LLMProviderFactory.create(settings.llm_provider)
        self._system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    async def analyze(self, user_message: str) -> LLMResponse:
        try:
            response = await self._provider.generate(
                system_prompt=self._system_prompt,
                user_message=user_message,
            )
            logger.info(
                "Analysis done: provider=%s, tokens=%d",
                settings.llm_provider,
                response.tokens_used,
            )
            return response
        except Exception:
            logger.exception("Analysis failed")
            raise

    async def continue_analysis(
        self, conversation_history: list[dict[str, str]], new_message: str
    ) -> LLMResponse:
        """Продолжить анализ с полным контекстом предыдущих сообщений."""
        messages = conversation_history + [{"role": "user", "content": new_message}]
        try:
            response = await self._provider.generate_with_history(
                system_prompt=self._system_prompt,
                messages=messages,
            )
            logger.info(
                "Continued analysis: provider=%s, tokens=%d",
                settings.llm_provider,
                response.tokens_used,
            )
            return response
        except Exception:
            logger.exception("Continue analysis failed")
            raise
