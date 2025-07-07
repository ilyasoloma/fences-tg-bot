from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent

from src.bot import bot
from src.db.repository import FencesMongo
from src.handlers import router as main_router
from src.utils.logger import logger


async def error_handler(event: ErrorEvent):
    logger.exception("An error occurred: %s", event.exception)


async def main():
    db = FencesMongo()
    await db.initialize_database()

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(main_router)
    dp.errors.register(error_handler)

    logger.info("🚀 Bot is running")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
