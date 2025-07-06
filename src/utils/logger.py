import logging
from logging.handlers import RotatingFileHandler
import os

LOG_FILE = "bot.log"
LOG_DIR = os.path.dirname(LOG_FILE)
os.makedirs(LOG_DIR, exist_ok=True) if LOG_DIR else None

logger = logging.getLogger("bot")
logger.setLevel(logging.INFO)

# Console handler
console = logging.StreamHandler()
console.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))

# File handler with rotation
file = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
file.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))

logger.addHandler(console)
logger.addHandler(file)
