import asyncio
from datetime import datetime

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent
from motor.motor_asyncio import AsyncIOMotorClient

from src.bot import bot
from src.config import config
from src.db.repository import FencesRepository
from src.middleware.access_control import AccessControlMiddleware
from src.routers import router
from src.services import FencesService
from src.utils.logger import logger


async def error_handler(event: ErrorEvent):
    logger.exception("An error occurred: %s", event.exception)


async def monitor_eol(service: FencesService):
    while True:
        eol = await service.get_eol_datetime()
        if eol and datetime.now() >= eol:
            service.mark_expired()
        else:
            service.mark_active()
        await asyncio.sleep(5)


async def main():
    client = AsyncIOMotorClient(config.MONGO_DB_URL)
    repo = FencesRepository(client)
    await repo.init_db()
    logger.info("Database initialized successfully")
    service = FencesService(repo)

    dp = Dispatcher(storage=MemoryStorage())
    dp["repo"] = repo
    dp["service"] = service

    dp.include_router(router)
    dp.errors.register(error_handler)

    dp.message.middleware(AccessControlMiddleware())
    dp.callback_query.middleware(AccessControlMiddleware())

    asyncio.create_task(monitor_eol(service))

    logger.info("🚀 Bot is running")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
