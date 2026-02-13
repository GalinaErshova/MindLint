from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_used: int


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_message: str) -> LLMResponse:
        ...

    @abstractmethod
    async def generate_with_history(
        self, system_prompt: str, messages: list[dict[str, str]]
    ) -> LLMResponse:
        """Генерация с полной историей сообщений [{"role": ..., "content": ...}, ...]."""
        ...
