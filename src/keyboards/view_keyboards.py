from aiogram.types import InlineKeyboardMarkup

from src.keyboards import btn


async def user_messages_keyboard(board: dict):
    buttons = [[btn(f"{k}", f"view:{k}")] for k in board.keys()]
    buttons.append([btn("📄 Получить файл", "download_messages"), btn("🔙 Главное меню", "back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_board_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[btn("🔙 Вернуться к списку", "view")]])
