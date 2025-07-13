from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from src.keyboards import btn
from src.services import FencesService


def main_menu_reply_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура с кнопкой для возврата в главное меню

    :return:
    :rtype: ReplyKeyboardMarkup
    """
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🏠 Главное меню")]], resize_keyboard=True,
                               one_time_keyboard=False)


async def main_menu(username: str, service: FencesService):
    base = []
    if not service.is_expired():
        base.append([btn("✏️ Написать на заборчике", "write")])
    base.append([btn("📬 Посмотреть свой заборчик", "view")])
    if await service.is_admin(username):
        base.append([btn("⚙ Управление", "admin")])
    return InlineKeyboardMarkup(inline_keyboard=base)


def message_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[btn("💾 Сохранить", "save"), btn("🔙 Отменить всё", "cancel")]])


def cancel_sending_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn('Сохранить и выйти в главное меню', "save"), btn('Выйти без сохранения', "try_cancel")],
        [btn('Вернуться и дополнить', "collect_msg")]])
