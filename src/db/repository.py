from typing import Optional, List, Dict, Any

from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient

from src.config import config
from src.db import models
from src.utils.logger import logger


class FencesMongo:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(FencesMongo, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.__config = config
        client: AsyncIOMotorClient = AsyncIOMotorClient(config.MONGO_DB_URL)
        self.db: AsyncIOMotorDatabase = client.fences

    async def initialize_database(self) -> None:
        logger.info("🍁 Starting initialize DB ")
        collections = await self.db.list_collection_names()
        if 'fences_bot_settings' not in collections:
            logger.info('Created collection "fences_bot_settings"')
            await self.db.fences_bot_settings.insert_one(models.Settings().model_dump())

        if 'fences_bot_messages' not in collections:
            logger.info('Created collection "fences_bot_messages"')
            await self.db.create_collection('fences_bot_messages')

        if self.__config.ADMIN_USERNAME:
            logger.info(f'Adding an admin from .env: {self.__config.ADMIN_USERNAME}')
            await self.add_admin(username=self.__config.ADMIN_USERNAME, label=self.__config.ADMIN_LABEL)

    async def get_settings(self) -> Optional[Dict[str, Any]]:
        return await self.db.fences_bot_settings.find_one({"name": "settings"})

    async def add_admin(self, username: str, label: Optional[str] = None) -> None:
        settings = await self.get_settings()
        if username not in settings['admins']:
            await self.db.fences_bot_settings.update_one({"name": "settings"}, {"$addToSet": {"admins": username}})
            await self.add_member(username, label)
        else:
            logger.info(f'🍁 The admin {username} has already been added')

    async def add_member(self, username: str, label: str) -> None:
        existing = await self.db.fences_bot_messages.find_one({"username": username})
        if not existing:
            user_entry = models.UserEntry(username=username, label=label).dict()

            await self.db.fences_bot_settings.update_one({"name": "settings"}, {"$addToSet": {"members": user_entry}})
            await self.db.fences_bot_messages.insert_one(models.MessageBoard(username=username).dict())

    async def get_members(self) -> List[dict]:
        settings = await self.get_settings()
        return settings.get("members", []) if settings else []

    async def get_admins(self) -> List[dict]:
        settings = await self.get_settings()
        return settings.get("admins", []) if settings else []

    async def save_message(self, recipient: str, alias: str, messages: List[Any]) -> None:
        message_entry = models.MessageEntry(alias=alias, parts=messages).dict()
        await self.db.fences_bot_messages.update_one({"username": recipient},
                                                     {"$addToSet": {"messages": message_entry}})

    async def get_messages(self, username: str) -> Dict[str, List[str]]:
        user_data = await self.db.fences_bot_messages.find_one({"username": username})
        if not user_data:
            return {}

        result = {}
        for message in user_data.get("messages", []):
            result[message["alias"]] = message["parts"]
        return result

    async def get_contacts(self) -> Dict[str, str]:
        members = await self.get_members()
        return {member["label"]: member["username"] for member in members}
