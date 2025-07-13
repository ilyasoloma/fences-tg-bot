import logging
from datetime import datetime
from typing import List, Dict, Optional, Literal

from aiogram import Bot

from src.config import config
from src.db import models
from src.db.models import Settings, UserEntry
from src.db.repository import FencesRepository
from src.utils.logger import logger


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

    async def check_alias_unique(self, recipient_label: str, alias: str) -> tuple[bool, Optional[str]]:
        contacts = await self.get_users(return_field='dict')
        recipient_username = contacts.get(recipient_label)
        if not recipient_username:
            return False, "❌ Получатель не найден"

        messages = await self.get_messages_by_username(recipient_username)
        if alias in messages:
            return False, f"❌ Псевдоним '{alias}' уже используется для сообщений этому получателю. Выбери другой."
        return True, None

    async def save_board(self, recipient_label: str, sender_alias: str, chunks: List[str],
                         sender_username: str | None = None) -> None:
        contacts = await self.get_users(return_field='dict')
        recipient_username = contacts.get(recipient_label)
        if recipient_username:
            await self.repo.save_message(recipient_username=recipient_username,
                                         sender_alias=sender_alias,
                                         parts=chunks,
                                         sender_username=sender_username)

    async def get_messages_by_username(self, username: str) -> Dict[str, List[str]]:
        return await self.repo.get_messages(username)

    async def get_user_label(self, username: str) -> Optional[str]:
        settings = await self._load_settings()
        for member in settings.members:
            if member.username == username:
                return member.label
        logger.warning("No label found for username %s", username)
        return None

    async def add_user(self, username: str, label: str, role: str, chat_id: int = 0) -> tuple[bool, Optional[str]]:
        settings = await self._load_settings()
        usernames = [m.username for m in settings.members]
        labels = [m.label for m in settings.members]

        if username in usernames:
            logger.warning("Attempt to add existing user %s", username)
            return False, "❌ Такой username уже есть"
        if label in labels:
            logger.warning("Attempt to add user with existing label %s", label)
            return False, "❌ Такое отображаемое имя уже используется"

        user = models.UserEntry(username=username, label=label, is_admin=(role == "admin"), chat_id=chat_id)
        await self.repo.add_member(user)
        await self._invalidate_cache()
        logger.info("Added user %s with label %s", username, label)
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

    async def send_bot_direct_message(self, bot: Bot, recipient_label: Optional[str],
                                      messages: List[Dict]) -> tuple[bool, Optional[str]]:
        contacts = await self.get_users(return_field='dict')
        failed_recipients = []

        async def send_message_to_chat(user_chat_id: int, message_dict: Dict) -> bool:
            try:
                if message_dict["type"] == "text":
                    await bot.send_message(chat_id=user_chat_id, text=message_dict["content"])
                elif message_dict["type"] == "photo":
                    await bot.send_photo(chat_id=user_chat_id, photo=message_dict["content"],
                                         caption=message_dict.get("caption"))
                elif message_dict["type"] == "video":
                    await bot.send_video(chat_id=user_chat_id, video=message_dict["content"],
                                         caption=message_dict.get("caption"))
                elif message_dict["type"] == "video_note":
                    await bot.send_video_note(chat_id=user_chat_id, video_note=message_dict["content"])
                elif message_dict["type"] == "audio":
                    await bot.send_audio(chat_id=user_chat_id, audio=message_dict["content"],
                                         caption=message_dict.get("caption"))
                elif message_dict["type"] == "sticker":
                    await bot.send_sticker(chat_id=user_chat_id, sticker=message_dict["content"])
                elif message_dict["type"] == "document":
                    await bot.send_document(chat_id=user_chat_id, document=message_dict["content"],
                                            caption=message_dict.get("caption"))
                elif message_dict["type"] == "voice":
                    await bot.send_voice(chat_id=user_chat_id, voice=message_dict["content"])
                else:
                    logger.warning("Unsupported message type: %s", message_dict["type"])
                    return False
                return True
            except Exception as e:
                logger.error("Failed to send %s message to chat_id %s: %s", message_dict["type"], user_chat_id, str(e))
                return False

        if recipient_label:
            if recipient_label not in contacts:
                logger.warning("Recipient %s not found in contacts", recipient_label)
                return False, f"❌ Получатель {recipient_label} не найден"
            chat_id = await self.repo.get_user_chat_id(recipient_label)
            if not chat_id or chat_id == 0:
                logger.warning("No chat_id for recipient %s", recipient_label)
                return False, f"❌ Не удалось отправить сообщение пользователю {recipient_label}: chat_id не найден"

            for message in messages:
                if not await send_message_to_chat(chat_id, message):
                    return False, f"❌ Ошибка отправки сообщения пользователю {recipient_label}"
            logger.info("Sent %d messages to %s (chat_id: %s)", len(messages), recipient_label, chat_id)
            return True, None
        else:
            # Отправка всем пользователям
            chat_ids = await self.repo.get_all_chat_ids()
            if not chat_ids:
                logger.warning("No users found for broadcast message")
                return False, "❌ Нет пользователей для отправки сообщения"

            for label, username in contacts.items():
                chat_id = await self.repo.get_user_chat_id(label)
                if not chat_id or chat_id == 0:
                    failed_recipients.append(label)
                    logger.warning("No chat_id for recipient %s", label)
                    continue

                for message in messages:
                    if not await send_message_to_chat(chat_id, message):
                        failed_recipients.append(label)
                        logger.error("Failed to send message to %s (chat_id: %s)", label, chat_id)
                        break

            if failed_recipients:
                return False, f"❌ Сообщение не отправлено пользователям: {', '.join(failed_recipients)}\n" \
                              f"Скорее всего, они еще ни разу не запускали бота 😢"
            logger.info("Sent %d messages to all users (%d recipients)", len(messages), len(chat_ids))
            return True, None
