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
    sender_username: str | None = None
    sender_alias: str
    parts: List[str]
    addition_time: datetime


class MessageBoard(BaseModel):
    username: str
    messages: List[MessageEntry] = []
