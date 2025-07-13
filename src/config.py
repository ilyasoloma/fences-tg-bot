import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    MONGO_DB_URL = os.getenv("MONGO_DB_URL", "mongodb://localhost:27017")
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
    START_CMD = 'Что вы хотите сделать?'
    SELECT_RECIPIENT = 'На чьем заборчике будем писать?'
    WRITE_ALIAS = "Как ты хочешь представиться?"
    ENTER_MESSAGE = 'Введите сообщение:'
    MESSAGE_SENT = '💾 Забочик сохранён!'
    ADDED_CHUNK = '✏️ Сообщение добавлено. Продолжай писать или нажми «💾 Сохранить».'
    WARNING_LEAVE_MSG = '⚠️Точно отменить отправку? Все несохранённые сбщ будут утеряны'

    EMPTY_BOARD = 'Пока ваш заборчик пуст'
    EMPTY_MSG = '❌ Сообщение пустое. Напиши что-нибудь.'
    NO_EMPTY_BOARD = 'Вот кто вам написал'
    EOL_BOARD = 'Это были все сообщения от пользователя:'
    EOL_DATETIME_MSG = "⏳ Время действия бота истекло."

    # Нештатное поведение
    ACCESS_DENIED = '🚫 Доступ запрещен! Кажется ты залез не в свой отряд'
    UNKNOWING_ERROR = "🧐 Либо я тебя не понял, либо где-то ошибся\n\n"
    ERROR_EMPTY_TEXT = '⚠️Йоу, здесь допускается только текстовое сообщение. Стикеры, аудио, и иной контент недопустим'

    # Управление
    MAIN_CONTROL_PANEL = "🔧 Меню управления ботом:"
    ADD_USER_ROLE = 'Кого вы хотите добавить?'
    ENTER_ADD_USERNAME = "Введите username (без @):"
    ENTER_ADD_ALIAS = "Введите отображаемое имя:"
    ADDING_USER = 'Добавление участника...'
    SET_DATETIME_MSG = 'Введите дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ:СС'

config = Config()
