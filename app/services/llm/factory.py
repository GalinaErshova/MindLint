from app.services.llm.base import BaseLLMProvider


class LLMProviderFactory:
    @staticmethod
    def create(provider_name: str) -> BaseLLMProvider:
        match provider_name:
            case "groq":
                from app.services.llm.groq import GroqProvider
                return GroqProvider()
            case "openai":
                from app.services.llm.openai import OpenAIProvider
                return OpenAIProvider()
            case "anthropic":
                from app.services.llm.anthropic import AnthropicProvider
                return AnthropicProvider()
            case _:
                raise ValueError(
                    f"Unknown LLM provider: '{provider_name}'. "
                    f"Supported: groq, openai, anthropic"
                )
