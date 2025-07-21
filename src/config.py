import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")

    # Получение учетных данных MongoDB
    MONGO_INITDB_ROOT_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME")
    MONGO_INITDB_ROOT_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
    MONGO_HOST = os.getenv("MONGO_HOST", "mongodb")
    MONGO_PORT = os.getenv("MONGO_PORT", "27017")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "fences")

    # Формирование MONGO_DB_URL с учетом учетных данных
    if MONGO_INITDB_ROOT_USERNAME and MONGO_INITDB_ROOT_PASSWORD:
        MONGO_DB_URL = os.getenv("MONGO_DB_URL",
                                 f"mongodb://{MONGO_INITDB_ROOT_USERNAME}:{MONGO_INITDB_ROOT_PASSWORD}"
                                 f"@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource=admin")
    else:
        error_msg = "Missing MONGO_INITDB_ROOT_USERNAME or MONGO_INITDB_ROOT_PASSWORD in .env"
        raise IOError(error_msg)

    DATETIME_PATTERN = '%d.%m.%Y %H:%M:%S'
    EOL_DATETIME = os.getenv('EOL_DATETIME', None)
    if EOL_DATETIME is not None:
        EOL_DATETIME = datetime.strptime(EOL_DATETIME.replace('_', ' '), DATETIME_PATTERN)

    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
    ADMIN_LABEL = os.getenv("ADMIN_LABEL")

    ALIAS_BYTE_LIMIT = 64
    LOG_FILE = os.getenv("LOG_FILE")
    LOG_DIR = os.path.dirname(LOG_FILE)
    LOG_LEVEL = os.getenv("LOG_LEVEL")


config = Config()
