# Тестирование подключения к LLM-провайдерам.
# Запуск: python test_llm.py
# Проверяет, что API-ключи валидны и провайдеры отвечают корректно.

import asyncio
from app.services.llm.factory import LLMProviderFactory

SYSTEM_PROMPT = "Ответь одним предложением."
USER_MESSAGE = "Привет, ты работаешь?"


async def test_provider(name: str) -> None:
    print(f"\n--- {name.upper()} ---")
    try:
        provider = LLMProviderFactory.create(name)
        response = await provider.generate(
            system_prompt=SYSTEM_PROMPT,
            user_message=USER_MESSAGE,
        )
        print(f"Ответ: {response.content}")
        print(f"Модель: {response.model}")
        print(f"Токены: {response.tokens_used}")
    except Exception as e:
        print(f"Ошибка: {e}")


async def main() -> None:
    # Groq (бесплатный)
    await test_provider("groq")

    # OpenAI (нужны кредиты)
    # await test_provider("openai")

    # Anthropic (нужны кредиты)
    # await test_provider("anthropic")


asyncio.run(main())
