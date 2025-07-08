from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent

from src.bot import bot
from src.db.repository import FencesMongo
from src.middleware.access_control import AccessControlMiddleware
from src.routers import router
from src.utils.logger import logger


async def error_handler(event: ErrorEvent):
    logger.exception("An error occurred: %s", event.exception)


async def main():
    db = FencesMongo()
    await db.initialize_database()

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    dp.errors.register(error_handler)
    dp.message.middleware(AccessControlMiddleware())
    dp.callback_query.middleware(AccessControlMiddleware())

    logger.info("🚀 Bot is running")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
