import logging
from datetime import datetime
from typing import List, Dict, Optional, Literal

from src.config import config
from src.db import models
from src.db.models import Settings, UserEntry
from src.db.repository import FencesRepository


class FencesService:
    def __init__(self, repo: FencesRepository):
        self.repo = repo
        self._expired = False
        self._settings_cache: Optional[Settings] = None

    async def _load_settings(self) -> Settings:
        if self._settings_cache is None:
            settings_dict = await self.repo.get_settings()
            self._settings_cache = Settings(**settings_dict) if settings_dict else Settings()
        return self._settings_cache

    async def _invalidate_cache(self):
        self._settings_cache = None
        logging.info('Settings cache is clear!')

    def is_expired(self) -> bool:
        return self._expired

    def mark_expired(self):
        self._expired = True

    def mark_active(self):
        self._expired = False

    async def is_allowed(self, username: str) -> bool:
        settings = await self._load_settings()
        return any(member.username == username for member in settings.members)

    async def is_admin(self, username: str) -> bool:
        settings = await self._load_settings()
        return any(member.username == username and member.is_admin for member in settings.members)

    async def get_users(self, role: Literal['all', 'admin', 'member'] = 'all',
                        return_field: Literal['username', 'label', 'dict'] = 'username'
                        ) -> List[UserEntry] | Dict[str, str]:
        logging.debug("Fetching users with role=%s, return_field=%s", role, return_field)
        settings = await self._load_settings()
        members = settings.members

        if role == 'admin':
            filtered = [m for m in members if m.is_admin]
        elif role == 'member':
            filtered = [m for m in members if not m.is_admin]
        else:
            filtered = members

        if return_field == 'dict':
            return {m.label: m.username for m in filtered}
        return [getattr(m, return_field) for m in filtered]

    async def save_board(self, recipient_label: str, sender_alias: str, chunks: List[str]) -> None:
        contacts = await self.get_users(return_field='dict')
        recipient_username = contacts.get(recipient_label)
        if recipient_username:
            await self.repo.save_message(recipient_username, sender_alias, chunks)

    async def get_messages_by_username(self, username: str) -> Dict[str, List[str]]:
        return await self.repo.get_messages(username)

    async def add_user(self, username: str, label: str, role: str) -> tuple[bool, Optional[str]]:
        settings = await self._load_settings()
        usernames = [m.username for m in settings.members]
        labels = [m.label for m in settings.members]

        if username in usernames:
            return False, "❌ Такой username уже есть"
        if label in labels:
            return False, "❌ Такое отображаемое имя уже используется"

        user = models.UserEntry(username=username, label=label, is_admin=(role == "admin"))
        await self.repo.add_member(user)
        await self._invalidate_cache()
        return True, None

    async def remove_user(self, alias: str) -> None:
        username = await self.repo.get_username_by_alias(alias)
        if username:
            await self.repo.remove_member(username)
            await self._invalidate_cache()

    async def set_admin_flag(self, admin_flag: bool, username: Optional[str] = None, alias: Optional[str] = None):
        if not username and alias:
            username = await self.repo.get_username_by_alias(alias)
        if username:
            await self.repo.set_admin_flag(username, admin_flag)
            await self._invalidate_cache()

    async def set_datetime(self, user_datetime: str) -> bool:
        try:
            parsed = datetime.strptime(user_datetime, config.DATETIME_PATTERN)
        except ValueError as e:
            logging.error(e)
            return False
        await self.repo.set_eol_datetime(parsed)
        await self._invalidate_cache()
        return True

    async def get_eol_datetime(self) -> datetime:
        settings = await self._load_settings()
        eol = settings.eol_datetime
        return eol
