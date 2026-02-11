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
