"""Конфигурация бота"""

import pytz
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Настройки времени
WARSAW_TZ = pytz.timezone('Europe/Warsaw')

# Токен бота из переменных окружения. Если не установлен — используем явный
# маркер чтобы основной модуль (`bot.py`) мог проверить и показать
# понятное сообщение пользователю instead of raising at import time.
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') or 'YOUR_BOT_TOKEN_HERE'
GROQ_TOKEN = os.getenv('GROQ_API_KEY')

# Настройки базы данных
DB_PATH = 'schedules.db'

# Логирование
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# Default level name; callers may pass this string to `logging` or resolve it
# to an integer level via `getattr(logging, LOG_LEVEL)`.
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Путь к БД можно переопределить через env
DB_PATH = os.getenv('SCHEDULES_DB_PATH', DB_PATH)