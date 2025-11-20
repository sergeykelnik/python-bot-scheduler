"""Основной модуль бота"""

import requests
import logging
import time
from database import Database
from scheduler import SchedulerManager
from handlers import MessageHandlers, user_states
from config import BOT_TOKEN, LOG_FORMAT, LOG_LEVEL

# Настройка логирования
logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        
        # Инициализация компонентов
        self.db = Database()
        self.scheduler = SchedulerManager(self)
        self.handlers = MessageHandlers(self)
        
        self.last_update_id = 0
    
    def send_message(self, chat_id, text, parse_mode='Markdown'):
        """Отправка сообщения в чат"""
        url = f"{self.base_url}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        try:
            response = requests.post(url, json=data)
            return response.json()
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None
    
    def send_scheduled_message(self, chat_id, message):
        """Отправка запланированного сообщения"""
        logger.info(f"Sending scheduled message to {chat_id}")
        self.send_message(chat_id, message)
    
    def get_updates(self, offset=None, timeout=30):
        """Получение обновлений от Telegram"""
        url = f"{self.base_url}/getUpdates"
        params = {'timeout': timeout, 'offset': offset}
        try:
            response = requests.get(url, params=params, timeout=timeout+5)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting updates: {e}")
            return None
    
    def process_update(self, update):
        """Обработка одного обновления"""
        if 'message' not in update:
            return
        
        message = update['message']
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        
        if 'text' not in message:
            return
        
        text = message['text']
        
        # Обработка команд
        if text.startswith('/'):
            command_parts = text.split()
            command = command_parts[0].split('@')[0]  # Удаляем username бота если присутствует
            args = command_parts[1:] if len(command_parts) > 1 else []
            
            if command == '/start':
                self.handlers.handle_start(chat_id, user_id)
            elif command == '/help':
                self.handlers.handle_help(chat_id, user_id)
            elif command == '/schedule':
                self.handlers.handle_schedule(chat_id, user_id)
            elif command == '/list':
                self.handlers.handle_list(chat_id, user_id)
            elif command == '/manage':
                self.handlers.handle_manage(chat_id, user_id)
            elif command == '/getchatid':
                self.handlers.handle_getchatid(chat_id, user_id)
        else:
            # Обработка обычных текстовых сообщений
            self.handlers.handle_text_message(chat_id, user_id, text)
    
    def start_polling(self):
        """Запуск опроса обновлений"""
        logger.info("Bot started! Press Ctrl+C to stop.")
        
        # Загрузка существующих расписаний из базы данных
        self.scheduler.load_schedules_from_db()
        
        # Запуск планировщика
        self.scheduler.start()
        
        try:
            while True:
                updates = self.get_updates(offset=self.last_update_id + 1)
                
                if updates and updates.get('ok'):
                    for update in updates.get('result', []):
                        self.last_update_id = update['update_id']
                        self.process_update(update)
                
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping bot...")
            self.scheduler.shutdown()

if __name__ == '__main__':
    import os
    
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("ОШИБКА: Пожалуйста, укажите токен бота!")
        print("Вариант 1: Установите переменную окружения")
        print("  $env:TELEGRAM_BOT_TOKEN='your_token_here'")
        print("Вариант 2: Замените 'YOUR_BOT_TOKEN_HERE' в config.py")
        exit(1)
    
    # Создание и запуск бота
    bot = TelegramBot(BOT_TOKEN)
    bot.start_polling()