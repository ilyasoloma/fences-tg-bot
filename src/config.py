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

    # Сообщения
    START_CMD = 'Что хочешь сделать?'
    MSG_START = 'К твоим услугам ✨'
    MSG_SELECT_RECIPIENT = 'На чьем заборчике будем писать?'
    MSG_WRITE_ALIAS = "Как ты хочешь представиться?\n\n" \
                      "Можно ввести свой псевдоним, либо воспользоваться таким, который присвоил админ"
    MSG_ENTER_MESSAGE = 'Введи сообщение:'
    MSG_MESSAGE_SENT = '💾 Забочик сохранён!'
    MSG_ADDED_CHUNK = '✏️ Сообщение добавлено. Продолжай писать или нажми «💾 Сохранить».'
    MSG_WARNING_LEAVE = '⚠️Точно отменить отправку? Все несохранённые сообщения будут утеряны'

    MSG_EMPTY_BOARD = 'Пока ваш заборчик пуст'
    MSG_EMPTY_MSG = '❌ Сообщение пустое. Напиши что-нибудь.'
    MSG_NO_EMPTY_BOARD = 'На твоем заборчике кое-что есть'
    MSG_EOL_BOARD = 'Это были все сообщения от пользователя:'
    MSG_EOL_DATETIME_MSG = "⏳ Время действия бота истекло."

    # Нештатное поведение
    ACCESS_DENIED = '🚫 Доступ запрещен! Кажется ты залез не в свой отряд'
    MSG_UNKNOWING_ERROR = "🧐 Либо я тебя не понял, либо что-то пошло не так. Имеет смысл сообщить админу\n"
    MSG_ERROR_EMPTY_TEXT = '⚠️Йоу, здесь допускается только текстовое сообщение. ' \
                           'Стикеры, аудио, и иной контент недопустим'

    # Управление
    MSG_MAIN_CONTROL_PANEL = "🔧 Меню управления ботом:"
    MSG_ADD_USER_ROLE = 'Кого ты хочешь добавить?'
    MSG_ENTER_ADD_USERNAME = "Введи username (без @):"
    MSG_ENTER_ADD_ALIAS = "Введи отображаемое имя:"
    MSG_ADDING_USER = 'Добавление участника...'
    MSG_SET_DATETIME = 'Введи дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ:СС'


config = Config()
