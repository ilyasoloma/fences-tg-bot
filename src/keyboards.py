from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.services import get_contacts


def btn(text, data):
    return InlineKeyboardButton(text=text, callback_data=data)


def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[[btn("✏️ Написать", "write")],
                                                 [btn("📬 Посмотреть", "view")]])


async def  recipient_keyboard():
    contacts = await get_contacts()
    return InlineKeyboardMarkup(inline_keyboard=[[btn(name, name)] for name in contacts] + [[btn("🔙 Назад", "back")]])


def back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[btn("🔙 Назад", "back")]])


def back_recipient():
    return InlineKeyboardMarkup(inline_keyboard=[[btn("Вернуться к списку", "view")]])


def message_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[btn("💾 Сохранить", "save")],
                                                 [btn("🔙 Отменить всё", "cancel")]])


def cancel_sending_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn('Сохранить и выйти в главное меню', "save"), btn('Выйти без сохранения', "main")],
        [btn('Вернуться и дополнить', "collect_msg")]
    ])


async def board_keyboard(board: dict):
    return InlineKeyboardMarkup(
        inline_keyboard=[[btn(f"{k}", f"view:{k}")] for k in board.keys()] + [[btn("🔙 Назад", "back")]]
    )


def back_to_board_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[btn("🔙 Вернуться к списку", "view")]])
