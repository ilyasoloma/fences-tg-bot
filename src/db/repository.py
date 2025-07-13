from datetime import datetime
from typing import Optional, List, Dict, Any

from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient

from src.config import config
from src.db import models
from src.db.models import UserEntry
from src.utils.logger import logger


class FencesRepository:
    def __init__(self, client: AsyncIOMotorClient):
        self.db: AsyncIOMotorDatabase = client.fences

    async def init_db(self):
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
                await self.add_member(user=UserEntry(username=config.ADMIN_USERNAME,
                                                     label=config.ADMIN_LABEL,
                                                     is_admin=True,
                                                     chat_id=0))
            else:
                logger.info("Admin user %s already exists", config.ADMIN_USERNAME)

    async def get_settings(self) -> Optional[Dict[str, Any]]:
        logger.debug("Fetching settings from DB")
        return await self.db.fences_bot_settings.find_one({"name": "settings"})

    async def update_settings(self, updates: Dict[str, Any]):
        await self.db.fences_bot_settings.update_one({"name": "settings"}, {"$set": updates})

    async def add_member(self, user: models.UserEntry):
        # Проверяем, существует ли пользователь с таким username
        existing_user = await self.db.fences_bot_settings.find_one(
            {"name": "settings", "members.username": user.username}
        )
        if existing_user:
            logger.warning("User with username %s already exists, skipping add_member", user.username)
            return

        await self.db.fences_bot_settings.update_one(
            {"name": "settings"},
            {"$addToSet": {"members": user.dict()}}
        )
        await self.db.fences_bot_messages.insert_one(models.MessageBoard(username=user.username).dict())
        logger.info("Added user %s to members", user.username)

    async def remove_member(self, username: str):
        await self.db.fences_bot_settings.update_one(
            {"name": "settings"},
            {"$pull": {"members": {"username": username}}}
        )
        await self.db.fences_bot_messages.delete_one({"username": username})
        logger.info("Removed user %s", username)

    async def set_admin_flag(self, username: str, is_admin: bool):
        await self.db.fences_bot_settings.update_one(
            {"name": "settings", "members.username": username},
            {"$set": {"members.$.is_admin": is_admin}}
        )
        logger.info("Set admin flag to %s for user %s", is_admin, username)

    async def set_eol_datetime(self, eol_datetime: datetime):
        await self.update_settings({"eol_datetime": eol_datetime})
        logger.info("Updated EOL datetime to %s", eol_datetime)

    async def get_eol_datetime(self) -> Optional[datetime]:
        settings = await self.get_settings()
        return settings.get("eol_datetime") if settings else None

    async def get_all_members(self) -> List[dict]:
        settings = await self.get_settings()
        return settings.get("members", []) if settings else []

    async def get_admins(self) -> List[dict]:
        return [m for m in await self.get_all_members() if m["is_admin"]]

    async def get_only_members(self) -> List[dict]:
        return [m for m in await self.get_all_members() if not m["is_admin"]]

    # --- Messages operations ---

    async def save_message(self, recipient_username: str, sender_alias: str, parts: List[str],
                           sender_username: str | None = None):
        entry = models.MessageEntry(sender_username=sender_username, sender_alias=sender_alias,
                                    parts=parts, addition_time=datetime.now())
        await self.db.fences_bot_messages.update_one({"username": recipient_username},
                                                     {"$addToSet": {"messages": entry.dict()}})

    async def get_messages(self, username: str) -> Dict[str, List[str]]:
        doc = await self.db.fences_bot_messages.find_one({"username": username})
        if not doc or "messages" not in doc:
            return {}

        return {msg["sender_alias"]: msg["parts"] for msg in doc["messages"]}

    async def get_username_by_alias(self, alias: str) -> Optional[str]:
        members = await self.get_all_members()
        for member in members:
            if member["label"] == alias:
                return member["username"]
        return None

    async def get_contacts(self) -> Dict[str, str]:
        return {member["label"]: member["username"] for member in await self.get_all_members()}

    # --- chat_id CRUD ---
    async def update_user_chat_id(self, username: str, chat_id: int):
        result = await self.db.fences_bot_settings.update_one(
            {"name": "settings", "members.username": username},
            {"$set": {"members.$.chat_id": chat_id}}
        )
        if result.matched_count == 0:
            logger.warning("No user found with username %s for chat_id update", username)
            return False
        logger.info("Updated chat_id to %s for user %s", chat_id, username)
        return True

    async def get_user_chat_id(self, label: str) -> Optional[int]:
        members = await self.get_all_members()
        for member in members:
            if member["label"] == label:
                return member["chat_id"]
        logger.warning("No user found with label %s for chat_id", label)
        return None

    async def get_all_chat_ids(self) -> List[int]:
        members = await self.get_all_members()
        chat_ids = [member["chat_id"] for member in members if member["chat_id"] != 0]
        logger.debug("Retrieved %d chat_ids", len(chat_ids))
        return chat_ids
