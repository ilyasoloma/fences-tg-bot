from typing import List, Literal
from pydantic import BaseModel


class UserEntry(BaseModel):
    username: str  # Telegram username (без @)
    label: str     # Отображаемое имя (например, "Маша 🌟")


class Settings(BaseModel):
    name: str = "settings"
    users: List[UserEntry] = []
    admins: List[str] = []  # список username-ов


class MessageEntry(BaseModel):
    alias: str
    parts: List[str]


class MessageBoard(BaseModel):
    username: str  # username получателя
    messages: List[MessageEntry] = []
