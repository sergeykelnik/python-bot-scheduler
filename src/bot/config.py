"""
Configuration module for the aiogram bot.
Loads environment variables and defines constants.
"""

import os
import logging

import pytz
from dotenv import load_dotenv

load_dotenv()

# Timezone
WARSAW_TZ = pytz.timezone("Europe/Warsaw")

# Tokens
BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
GROQ_TOKEN: str | None = os.getenv("GROQ_API_KEY")

# Database
DB_PATH: str = os.getenv("SCHEDULES_DB_PATH", "schedules.db")

# Logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL_STR = os.getenv("LOG_LEVEL", "INFO")

try:
    LOG_LEVEL = getattr(logging, LOG_LEVEL_STR.upper())
except AttributeError:
    LOG_LEVEL = logging.INFO

logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)

