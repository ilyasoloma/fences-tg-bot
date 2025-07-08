from typing import Callable, Awaitable, Any, Dict, Union

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from src.config import config
from src.services import is_allowed
from src.utils.logger import logger


class AccessControlMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
                       event: Union[Message, CallbackQuery], data: Dict[str, Any]) -> Any:

        if isinstance(event, CallbackQuery) and event.data.startswith(('admin', 'add_user_', 'rm_')):
            return await handler(event, data)

        username = event.from_user.username
        if not await is_allowed(username):
            if isinstance(event, Message):
                logger.warning("[ACCESS DENIED] @%s tried to send: %r", username, event.text)
                await event.answer(config.ACCESS_DENIED)
            elif isinstance(event, CallbackQuery):
                logger.warning("[ACCESS DENIED] @%s tried to press: %r", username, event.data)
                await event.message.edit_text(config.ACCESS_DENIED)
            return

        return await handler(event, data)
