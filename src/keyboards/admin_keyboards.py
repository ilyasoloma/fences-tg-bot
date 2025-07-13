from typing import Literal

from aiogram.types import InlineKeyboardMarkup

from src.keyboards import btn
from src.services import FencesService


def admin_panel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn("➕ Добавить участника", "admin_add"), btn("➖ Удалить участника", "admin_remove_member")],
        [btn('👨‍🚀 Выдать права администратора', 'add_root'), btn("🤐 Отозвать права администратора", "delete_root")],
        [btn('⏱️Изменить время действия бота', 'set_datetime'),
         btn('📢 Отправить сообщение от бота', 'send_bot_message')],
        [btn("🔙 Назад", "back")]])


async def choose_user_to_remove_keyboard(service: FencesService, role: Literal['all', 'admin', 'member'] = 'all'):
    usernames, _ = await service.get_users(role=role, return_field='label')
    rows = [[btn(f"{u}", f"rm_user:{u}")] for u in usernames]
    rows.append([btn("🔙 Назад", "admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def bot_message_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[btn("Всем пользователям", "bot_message_all")],
                                                 [btn("Конкретному пользователю", "bot_message_single")],
                                                 [btn("🔙 Назад", "admin")]])


async def bot_message_recipient_keyboard(service: FencesService):
    contacts, _ = await service.get_users(return_field='dict')
    return InlineKeyboardMarkup(
        inline_keyboard=[[btn(name, f"bot_recipient:{name}")] for name in contacts] + [[btn("🔙 Назад", "admin")]])
