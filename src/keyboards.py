from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.services import get_contacts, is_admin


def btn(text, data):
    return InlineKeyboardButton(text=text, callback_data=data)


async def main_menu(username: str):
    base = [[btn("✏️ Написать", "write")], [btn("📬 Посмотреть", "view")]]
    if await is_admin(username):
        base.append([btn("⚙ Управление", "admin")])
    return InlineKeyboardMarkup(inline_keyboard=base)


async def recipient_keyboard():
    contacts = await get_contacts()
    return InlineKeyboardMarkup(inline_keyboard=[[btn(name, name)] for name in contacts] + [[btn("🔙 Назад", "back")]])


def back_keyboard(data:str = 'back'):
    return InlineKeyboardMarkup(inline_keyboard=[[btn(f"🔙 Назад", data)]])


def back_recipient():
    return InlineKeyboardMarkup(inline_keyboard=[[btn("Вернуться к списку", "view")]])


def message_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[btn("💾 Сохранить", "save")],
                                                 [btn("🔙 Отменить всё", "cancel")]])


def cancel_sending_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn('Сохранить и выйти в главное меню', "save"), btn('Выйти без сохранения', "try_cancel")],
        [btn('Вернуться и дополнить', "collect_msg")]
    ])


async def user_messages_keyboard(board: dict):
    return InlineKeyboardMarkup(
        inline_keyboard=[[btn(f"{k}", f"view:{k}")] for k in board.keys()] + [[btn("🔙 Назад", "back")]]
    )


def back_to_board_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[btn("🔙 Вернуться к списку", "view")]])


def admin_panel_keyboad():
    return InlineKeyboardMarkup(inline_keyboard=[[btn("➕ Добавить участника", "admin_add")],
                                                 [btn("➖ Удалить участника", "admin_remove_member")],
                                                 [btn("✉️ Написать сообщение", "admin_send_message")],
                                                 [btn("🔙 Назад", "back")]])


def admin_ask_user_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[btn("👤 Участник", "add_user")],
                                                 [btn("🛡 Админ", "add_admin")],
                                                 [btn("🔙 Назад", "admin_back")]])


async def choose_user_to_remove_keyboard(usernames):
    rows = [[btn(f"❌ {u}", f"rm_user:{u}")] for u in usernames.keys()]
    rows.append([btn("🔙 Назад", "admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
