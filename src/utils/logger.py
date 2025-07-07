import logging
import os
from logging.handlers import RotatingFileHandler

from src.config import config

os.makedirs(config.LOG_DIR, exist_ok=True) if config.LOG_DIR else None

logger = logging.getLogger("bot")
logger.setLevel(level=config.LOG_LEVEL)

console = logging.StreamHandler()
console.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))

file = RotatingFileHandler(config.LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
file.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))

logger.addHandler(console)
logger.addHandler(file)
