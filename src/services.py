from typing import List, Dict

from src.db.repository import FencesMongo

db = FencesMongo()


async def is_allowed(username: str) -> bool:
    contacts = await db.get_contacts()
    return username in contacts.values()


async def is_admin(username: str) -> bool:
    settings = await db.get_settings()
    return username in settings.get("admins", [])


async def save_board(user_label: str, sender: str, chunks: List[str]):
    contacts = await db.get_contacts()
    await db.save_message(contacts[user_label], sender, chunks)


async def get_messages_by_username(username: str) -> dict:
    return await db.get_messages(username)


async def get_contacts(type_users: str = 'all') -> Dict[str, str]:
    if type_users == 'all':
        return await db.get_contacts()
    elif type_users == 'members':
        admins = await db.get_admins()
        members = await db.get_members()
        result = {}
        for member in members:
            if member['username'] not in admins:
                result[member['label']] = member['username']
        return result
    else:
        admins = await db.get_admins()
        members = await db.get_members()
        result = {}
        for member in members:
            if member['username'] in admins:
                result[member['label']] = admins
        return result


async def add_user(username: str, label: str, role: str) -> tuple[bool, str]:
    from src.db.models import UserEntry

    # Проверка username и label на дубликаты
    settings = await db.get_settings()
    usernames = [u["username"] for u in settings.get("members", [])]
    labels = [u["label"] for u in settings.get("members", [])]

    if username in usernames:
        return False, "❌ Такой username уже есть"

    if label in labels:
        return False, "❌ Такое отображаемое имя уже используется"

    entry = UserEntry(username=username, label=label)

    if role == "admin":
        await db.add_admin(username=username, label=label)
    else:
        await db.add_member(username=username, label=label)

    return True, None


async def get_users_by_role(role: str) -> list[str]:
    settings = await db.get_settings()
    if role == "admin":
        return settings["admins"]
    elif role == "member":
        all_members = [m["username"] for m in settings.get("members", [])]
        return [u for u in all_members if u not in settings["admins"]]
    return []


async def remove_user(username: str):
    await db.remove_user(username)
