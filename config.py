"""Конфигурация бота"""

import pytz
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Настройки времени
WARSAW_TZ = pytz.timezone('Europe/Warsaw')

# Токен бота из переменных окружения
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Настройки базы данных
DB_PATH = 'schedules.db'

# Логирование
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'

# Проверка токена
if not BOT_TOKEN or BOT_TOKEN == 'your_actual_bot_token_here':
    raise ValueError("TELEGRAM_BOT_TOKEN not set in .env file")