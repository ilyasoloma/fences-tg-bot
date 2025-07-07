from typing import List, Dict

from src.config import config
from src.db.repository import FencesMongo

db = FencesMongo()


async def is_allowed(username: str) -> bool:
    contacts = await db.get_contacts()
    return username in contacts.values()


async def save_board(user_label: str, sender: str, chunks: List[str]):
    contacts = await db.get_contacts()
    await db.save_message(contacts[user_label], sender, chunks)


async def load_board(username: str) -> dict:
    return await db.get_messages(username)


async def get_contacts() -> Dict[str, str]:
    return await db.get_contacts()


def validate_alias(alias: str, max_bytes: int = config.ALIAS_BYTE_LIMIT) -> tuple[bool, str | None]:
    alias = alias.strip()
    try:
        encoded = alias.encode("utf-8")
    except UnicodeEncodeError:
        return False, "❌ Некорректные символы. Попробуйте другое имя."

    if len(encoded) > max_bytes:
        return False, f"❌ Слишком длинное имя — занимает {len(encoded)} байт. Разрешено до {max_bytes}."

    return True, None
