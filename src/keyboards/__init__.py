from aiogram.types import InlineKeyboardButton


def btn(text, data):
    return InlineKeyboardButton(text=text, callback_data=data)