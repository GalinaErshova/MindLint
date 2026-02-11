import asyncio
import logging

from app.config import settings
from app.utils.logging_config import setup_logging
from app.bot import create_bot, create_dispatcher

logger = logging.getLogger(__name__)


async def main() -> None:
    setup_logging(settings.log_level)
    logger.info("Starting MindLint bot...")

    bot = create_bot()
    dp = create_dispatcher()

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
