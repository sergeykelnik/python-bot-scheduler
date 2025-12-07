"""
Configuration module for the bot.
Loads environment variables and defines constants.
"""

import os
import pytz
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Timezone settings
WARSAW_TZ = pytz.timezone('Europe/Warsaw')

# Bot Token from environment variables.
# Using a placeholder to avoid import errors, but runtime check should handle it.
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') or 'YOUR_BOT_TOKEN_HERE'
GROQ_TOKEN = os.getenv('GROQ_API_KEY')

# Database settings
DB_PATH = os.getenv('SCHEDULES_DB_PATH', 'schedules.db')

# Logging settings
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL_STR = os.getenv('LOG_LEVEL', 'INFO')

# Resolve logging level to integer
try:
    LOG_LEVEL = getattr(logging, LOG_LEVEL_STR.upper())
except AttributeError:
    LOG_LEVEL = logging.INFO
