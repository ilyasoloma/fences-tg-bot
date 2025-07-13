from io import StringIO
from typing import Dict, List

from src.config import config


def validate_alias(alias: str, max_bytes: int = config.ALIAS_BYTE_LIMIT) -> tuple[bool, str | None]:
    alias = alias.strip()
    try:
        encoded = alias.encode("utf-8")
    except UnicodeEncodeError:
        return False, "❌ Некорректные символы. Попробуйте другое имя."

    if len(encoded) > max_bytes:
        return False, f"❌ Слишком длинное имя — занимает {len(encoded)} байт. Разрешено до {max_bytes}."

    return True, None


def prepared_msg_file(board: Dict[str, List[str]]) -> StringIO:
    file_content = StringIO()
    for alias, messages in board.items():
        file_content.write(f"{alias}:\n")
        for msg in messages:
            file_content.write(f" {msg}\n\n")

        file_content.write("____________\n")
    return file_content
