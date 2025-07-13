from datetime import datetime
from typing import List

from pydantic import BaseModel


class UserEntry(BaseModel):
    username: str  # Telegram username (без @)
    label: str  # Отображаемое имя
    chat_id: int | None = None
    is_admin: bool


class Settings(BaseModel):
    name: str = "settings"
    members: List[UserEntry] = []
    eol_datetime: datetime | None = None


class MessageEntry(BaseModel):
    alias: str
    parts: List[str]


class MessageBoard(BaseModel):
    username: str
    messages: List[MessageEntry] = []
