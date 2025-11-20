"""Конфигурация бота"""

import pytz
import os

# Настройки времени
WARSAW_TZ = pytz.timezone('Europe/Warsaw')

# Токен бота
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# Настройки базы данных
DB_PATH = 'schedules.db'

# Логирование
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'