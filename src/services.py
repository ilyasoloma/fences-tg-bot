from datetime import datetime
from typing import List, Dict, Optional

from src.config import config
from src.db import models
from src.db.repository import FencesRepository


class FencesService:
    def __init__(self, repo: FencesRepository):
        self.repo = repo

    async def is_allowed(self, username: str) -> bool:
        contacts = await self.repo.get_contacts()
        return username in contacts.values()

    async def is_admin(self, username: str) -> bool:
        admins = await self.repo.get_admins()
        return any(admin["username"] == username for admin in admins)

    async def get_contacts(self, type_users: str = 'all') -> Dict[str, str]:
        if type_users == 'all':
            return await self.repo.get_contacts()
        elif type_users == 'members':
            members = await self.repo.get_only_members()
            return {m["label"]: m["username"] for m in members}
        elif type_users == 'admins':
            admins = await self.repo.get_admins()
            return {a["label"]: a["username"] for a in admins}
        return {}

    async def save_board(self, recipient_label: str, sender_alias: str, chunks: List[str]) -> None:
        contacts = await self.repo.get_contacts()
        recipient_username = contacts.get(recipient_label)
        if recipient_username:
            await self.repo.save_message(recipient_username, sender_alias, chunks)

    async def get_messages_by_username(self, username: str) -> Dict[str, List[str]]:
        return await self.repo.get_messages(username)

    async def add_user(self, username: str, label: str, role: str) -> tuple[bool, Optional[str]]:
        settings = await self.repo.get_settings()
        members = settings.get("members", []) if settings else []

        usernames = [m["username"] for m in members]
        labels = [m["label"] for m in members]

        if username in usernames:
            return False, "❌ Такой username уже есть"
        if label in labels:
            return False, "❌ Такое отображаемое имя уже используется"

        user = models.UserEntry(username=username, label=label, is_admin=(role == "admin"))
        await self.repo.add_member(user)
        return True, None

    async def get_users_by_role(self, role: str, returning: str = 'label') -> List[str]:
        if role == 'admin':
            users = await self.repo.get_admins()
        elif role == 'member':
            users = await self.repo.get_only_members()
        elif role == 'all':
            users = await self.repo.get_all_members()
        else:
            return []

        return [u[returning] for u in users if returning in u]

    async def remove_user(self, alias: str) -> None:
        username = await self.repo.get_username_by_alias(alias)
        if username:
            await self.repo.remove_member(username)

    async def set_admin_flag(self, admin_flag: bool, username: Optional[str] = None, alias: Optional[str] = None):
        if not username and alias:
            username = await self.repo.get_username_by_alias(alias)
        if username:
            await self.repo.set_admin_flag(username, admin_flag)

    async def set_datetime(self, user_datetime: str) -> bool:
        try:
            parsed = datetime.strptime(user_datetime, config.DATETIME_PATTERN)
        except ValueError:
            return False
        await self.repo.set_eol_datetime(parsed)
        return True

    async def is_eol_date(self) -> bool:
        eol = await self.repo.get_eol_datetime()
        return bool(eol and eol < datetime.now())
