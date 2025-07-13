from typing import Callable, Awaitable, Any, Dict, Union

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from src.config import config
from src.services import FencesService
from src.utils.logger import logger


class AccessControlMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
                       event: Union[Message, CallbackQuery], data: Dict[str, Any]) -> Any:

        if isinstance(event, CallbackQuery) and event.data.startswith(('admin', 'add_user_', 'rm_')):
            return await handler(event, data)

        username = event.from_user.username
        service: FencesService = data["service"]

        if not await service.is_allowed(username):
            logger.warning("[ACCESS DENIED] @%s", username)
            text = config.ACCESS_DENIED
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery):
                await event.message.edit_text(text)
            return

        return await handler(event, data)
