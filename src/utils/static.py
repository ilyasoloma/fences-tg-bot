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