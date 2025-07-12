from typing import List, Dict

from src.db.repository import FencesMongo

db = FencesMongo()


async def is_allowed(username: str) -> bool:
    contacts = await db.get_contacts()
    return username in contacts.values()


async def is_admin(username: str) -> bool:
    admin_list = await db.get_admins()
    if not admin_list:
        return False
    admin_username_list = [usr['username'] for usr in admin_list]
    return username in admin_username_list


async def save_board(user_label: str, sender: str, chunks: List[str]):
    contacts = await db.get_contacts()
    await db.save_message(contacts[user_label], sender, chunks)


async def get_messages_by_username(username: str) -> dict:
    return await db.get_messages(username)


async def get_contacts(type_users: str = 'all') -> Dict[str, str]:
    if type_users == 'all':
        return await db.get_contacts()
    elif type_users == 'members':
        members = await db.get_only_members()
        return {member["label"]: member["username"] for member in members}
    else:
        admins = await db.get_admins()
        return {admin["label"]: admin["username"] for admin in admins}


async def add_user(username: str, label: str, role: str) -> tuple[bool, str | None]:
    # Проверка username и label на дубликаты
    settings = await db.get_settings()
    usernames = [u["username"] for u in settings.get("members", [])]
    labels = [u["label"] for u in settings.get("members", [])]

    if username in usernames:
        return False, "❌ Такой username уже есть"

    if label in labels:
        return False, "❌ Такое отображаемое имя уже используется"

    await db.add_member(username=username, label=label, is_admin=role == "admin")

    return True, None


async def get_users_by_role(role: str, returning_type: str = 'label') -> list[str]:
    if role == "admin":
        admins = await db.get_admins()
        return [a[returning_type] for a in admins]
    elif role == "member":
        users = await db.get_only_members()
        return [a[returning_type] for a in users]
    elif role == 'all':
        users = await db.get_all_members()
        return [a[returning_type] for a in users]
    return []


async def remove_user(alias: str):
    await db.remove_user(alias=alias)


async def set_admin_flag(admin_flag: bool, username: str | None = None, alias: str | None = None):
    await db.set_admin_flag(admin_flag=admin_flag, username=username, alias=alias)