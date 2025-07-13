from aiogram.types import InlineKeyboardMarkup

from src.keyboards import btn
from src.services import FencesService


async def recipient_keyboard(service: FencesService):
    contacts, _ = await service.get_users(return_field='dict')
    return InlineKeyboardMarkup(inline_keyboard=[[btn(name, name)] for name in contacts] + [[btn("🔙 Назад", "back")]])


def entry_alias_keyboard(data: str = 'back'):
    return InlineKeyboardMarkup(inline_keyboard=[[btn("👤 Как в списке", "use_label"), btn("🔙 Назад", data)]])


def back_keyboard(data: str = 'back'):
    return InlineKeyboardMarkup(inline_keyboard=[[btn("🔙 Назад", data)]])
