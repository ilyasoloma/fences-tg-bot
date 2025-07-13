from datetime import datetime
from typing import Optional, List, Dict, Any

from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, PyMongoError

from src.config import config
from src.db import models
from src.db.models import UserEntry
from src.utils.logger import logger


class FencesRepository:
    def __init__(self, client: AsyncIOMotorClient):
        self.db: AsyncIOMotorDatabase = client.fences

    async def init_db(self) -> tuple[bool, Optional[str]]:
        """
        Инициализация БД:
            1. Проверка наличия необходимых коллекций
            2. Добавление индексации
            3. Добавление админа при необходимости

        :return: кортеж со статусом инициализации и трейсбеком ошибки при необходимости
        :rtype:
        """
        try:
            logger.info("🍁 Initializing DB...")
            collections = await self.db.list_collection_names()

            if "fences_bot_settings" not in collections:
                logger.info("Creating 'fences_bot_settings' collection...")
                settings = models.Settings().dict()
                settings["eol_datetime"] = config.EOL_DATETIME
                await self.db.fences_bot_settings.insert_one(settings)
                await self.db.fences_bot_settings.create_index("name")

            if "fences_bot_messages" not in collections:
                logger.info("Creating 'fences_bot_messages' collection...")
                await self.db.create_collection("fences_bot_messages")
                await self.db.fences_bot_messages.create_index("username")

            if config.ADMIN_USERNAME is not None:
                existing_user = await self.db.fences_bot_settings.find_one({"name": "settings",
                                                                            "members.username": config.ADMIN_USERNAME})
                if not existing_user:
                    logger.info("Adding admin user %s", config.ADMIN_USERNAME)
                    success, error = await self.add_member(user=UserEntry(username=config.ADMIN_USERNAME,
                                                                          label=config.ADMIN_LABEL,
                                                                          is_admin=True,
                                                                          chat_id=0))
                    if not success:
                        return False, error
                else:
                    logger.info("Admin user %s already exists", config.ADMIN_USERNAME)
            return True, None
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error("Database connection error: %s", str(e))
            return False, config.MSG_UNKNOWING_ERROR
        except PyMongoError as e:
            logger.error("Database error during init_db: %s", str(e))
            return False, config.MSG_UNKNOWING_ERROR

    async def get_settings(self) -> Optional[Dict[str, Any]]:
        """
        Получить документ с настройками
        :return: содержимое документа настроек в словаре
        :rtype:
        """

        try:
            logger.debug("Fetching settings from DB")
            return await self.db.fences_bot_settings.find_one({"name": "settings"})
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error("Database connection error in get_settings: %s", str(e))
            return None
        except PyMongoError as e:
            logger.error("Database error in get_settings: %s", str(e))
            return None

    async def update_settings(self, updates: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Обновить файл настроек в БД

        :param updates: обновленный файл настроек
        :type updates:
        :return: кортеж с результатом и трейсбеком ошибки при необходимости
        :rtype:
        """
        try:
            await self.db.fences_bot_settings.update_one({"name": "settings"}, {"$set": updates})
            return True, None
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error("Database connection error in update_settings: %s", str(e))
            return False, config.MSG_UNKNOWING_ERROR
        except PyMongoError as e:
            logger.error("Database error in update_settings: %s", str(e))
            return False, config.MSG_UNKNOWING_ERROR

    async def add_member(self, user: models.UserEntry) -> tuple[bool, Optional[str]]:
        """
        Добавить пользователя в БД

        :param user:
        :type user:
        :return:
        :rtype:
        """
        try:
            existing_user = await self.db.fences_bot_settings.find_one(
                {"name": "settings", "members.username": user.username}
            )
            if existing_user:
                logger.warning("User with username %s already exists, skipping add_member", user.username)
                return False, "❌ Такой username уже есть"

            await self.db.fences_bot_settings.update_one(
                {"name": "settings"},
                {"$addToSet": {"members": user.dict()}}
            )
            await self.db.fences_bot_messages.insert_one(models.MessageBoard(username=user.username).dict())
            logger.info("Added user %s to members", user.username)
            return True, None
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error("Database connection error in add_member: %s", str(e))
            return False, config.MSG_UNKNOWING_ERROR
        except PyMongoError as e:
            logger.error("Database error in add_member: %s", str(e))
            return False, config.MSG_UNKNOWING_ERROR

    async def remove_member(self, username: str) -> tuple[bool, Optional[str]]:
        """
        Удалить пользователя. Удаляет и запись в settings и документ из коллекции fences_bot_messages

        :param username:
        :type username:
        :return:
        :rtype:
        """
        try:
            await self.db.fences_bot_settings.update_one(
                {"name": "settings"},
                {"$pull": {"members": {"username": username}}}
            )
            await self.db.fences_bot_messages.delete_one({"username": username})
            logger.info("Removed user %s", username)
            return True, None
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error("Database connection error in remove_member: %s", str(e))
            return False, config.MSG_UNKNOWING_ERROR
        except PyMongoError as e:
            logger.error("Database error in remove_member: %s", str(e))
            return False, config.MSG_UNKNOWING_ERROR

    async def set_admin_flag(self, username: str, is_admin: bool) -> tuple[bool, Optional[str]]:
        """
        Изменить флаг админа у пользователя username

        :param username:
        :type username:
        :param is_admin:
        :type is_admin:
        :return:
        :rtype:
        """
        try:
            await self.db.fences_bot_settings.update_one(
                {"name": "settings", "members.username": username},
                {"$set": {"members.$.is_admin": is_admin}}
            )
            logger.info("Set admin flag to %s for user %s", is_admin, username)
            return True, None
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error("Database connection error in set_admin_flag: %s", str(e))
            return False, config.MSG_UNKNOWING_ERROR
        except PyMongoError as e:
            logger.error("Database error in set_admin_flag: %s", str(e))
            return False, config.MSG_UNKNOWING_ERROR

    async def set_eol_datetime(self, eol_datetime: datetime) -> tuple[bool, Optional[str]]:
        """
        Изменить время действия бота

        :param eol_datetime:
        :type eol_datetime:
        :return:
        :rtype:
        """
        try:
            await self.update_settings({"eol_datetime": eol_datetime})
            logger.info("Updated EOL datetime to %s", eol_datetime)
            return True, None
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error("Database connection error in set_eol_datetime: %s", str(e))
            return False, config.MSG_UNKNOWING_ERROR
        except PyMongoError as e:
            logger.error("Database error in set_eol_datetime: %s", str(e))
            return False, config.MSG_UNKNOWING_ERROR

    async def get_eol_datetime(self) -> Optional[datetime]:
        """
        Получить время действия бота

        :return:
        :rtype:
        """
        try:
            settings = await self.get_settings()
            return settings.get("eol_datetime") if settings else None
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error("Database connection error in get_eol_datetime: %s", str(e))
            return None
        except PyMongoError as e:
            logger.error("Database error in get_eol_datetime: %s", str(e))
            return None

    async def get_all_members(self) -> List[dict]:
        """
        Получить всех пользователей списком

        :return:
        :rtype:
        """
        try:
            settings = await self.get_settings()
            return settings.get("members", []) if settings else []
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error("Database connection error in get_all_members: %s", str(e))
            return []
        except PyMongoError as e:
            logger.error("Database error in get_all_members: %s", str(e))
            return []

    async def save_message(self, recipient_username: str, sender_alias: str, parts: List[str],
                           sender_username: str | None = None) -> tuple[bool, Optional[str]]:
        """
        Сохранить сообщение на заборчике recipient_username
        """
        try:
            entry = models.MessageEntry(sender_username=sender_username, sender_alias=sender_alias,
                                        parts=parts, addition_time=datetime.now())
            await self.db.fences_bot_messages.update_one(
                {"username": recipient_username},
                {"$addToSet": {"messages": entry.dict()}}
            )
            logger.info("Saved message for recipient %s from sender %s (alias: %s)", recipient_username,
                        sender_username or "unknown", sender_alias)
            return True, None
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error("Database connection error in save_message: %s", str(e))
            return False, config.MSG_UNKNOWING_ERROR
        except PyMongoError as e:
            logger.error("Database error in save_message: %s", str(e))
            return False, config.MSG_UNKNOWING_ERROR

    async def get_messages(self, username: str) -> Dict[str, List[str]]:
        """
        Получить все сообщения для пользователя username

        :param username:
        :type username:
        :return:
        :rtype:
        """
        try:
            doc = await self.db.fences_bot_messages.find_one({"username": username})
            if not doc or "messages" not in doc:
                return {}
            return {msg["sender_alias"]: msg["parts"] for msg in doc["messages"]}
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error("Database connection error in get_messages: %s", str(e))
            return {}
        except PyMongoError as e:
            logger.error("Database error in get_messages: %s", str(e))
            return {}

    async def get_username_by_alias(self, alias: str) -> Optional[str]:
        """
        Получить username по alias

        :param alias:
        :type alias:
        :return:
        :rtype:
        """
        try:
            members = await self.get_all_members()
            for member in members:
                if member["label"] == alias:
                    return member["username"]
            return None
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error("Database connection error in get_username_by_alias: %s", str(e))
            return None
        except PyMongoError as e:
            logger.error("Database error in get_username_by_alias: %s", str(e))
            return None

    async def update_user_chat_id(self, username: str, chat_id: int) -> tuple[bool, Optional[str]]:
        """
        Обновить chat_id для пользователя username

        :param username:
        :type username:
        :param chat_id:
        :type chat_id:
        :return:
        :rtype:
        """
        try:
            result = await self.db.fences_bot_settings.update_one(
                {"name": "settings", "members.username": username},
                {"$set": {"members.$.chat_id": chat_id}}
            )
            if result.matched_count == 0:
                logger.warning("No user found with username %s for chat_id update", username)
                return False, "❌ Пользователь не найден"
            logger.info("Updated chat_id to %s for user %s", chat_id, username)
            return True, None
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error("Database connection error in update_user_chat_id: %s", str(e))
            return False, config.MSG_UNKNOWING_ERROR
        except PyMongoError as e:
            logger.error("Database error in update_user_chat_id: %s", str(e))
            return False, config.MSG_UNKNOWING_ERROR

    async def get_user_chat_id(self, label: str) -> Optional[int]:
        """
        Получить пользовательский chat_id
        """
        try:
            members = await self.get_all_members()
            for member in members:
                if member["label"] == label:
                    return member["chat_id"]
            logger.warning("No user found with label %s for chat_id", label)
            return None
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error("Database connection error in get_user_chat_id: %s", str(e))
            return None
        except PyMongoError as e:
            logger.error("Database error in get_user_chat_id: %s", str(e))
            return None

    async def get_all_chat_ids(self) -> List[int]:
        """
        Получить все не нулевые chat_id
        """
        try:
            members = await self.get_all_members()
            chat_ids = [member["chat_id"] for member in members if member["chat_id"] != 0]
            logger.debug("Retrieved %d chat_ids", len(chat_ids))
            return chat_ids
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error("Database connection error in get_all_chat_ids: %s", str(e))
            return []
        except PyMongoError as e:
            logger.error("Database error in get_all_chat_ids: %s", str(e))
            return []
