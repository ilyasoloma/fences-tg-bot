from datetime import datetime
from typing import List, Literal
from pydantic import BaseModel


class UserEntry(BaseModel):
    username: str  # Telegram username (без @)
    label: str     # Отображаемое имя
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
