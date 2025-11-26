"""Основной модуль бота"""

import requests
import logging
import time
from database import Database
from scheduler import SchedulerManager
from handlers import MessageHandlers, user_states
from translations import Translator
from config import BOT_TOKEN, LOG_FORMAT, LOG_LEVEL

# Настройка логирования — поддерживаем как строковые, так и числовые уровни
log_level = getattr(logging, LOG_LEVEL) if isinstance(LOG_LEVEL, str) else LOG_LEVEL
logging.basicConfig(format=LOG_FORMAT, level=log_level)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        
        # Инициализация компонентов
        self.translator = Translator()
        self.db = Database()
        self.scheduler = SchedulerManager(self)
        self.handlers = MessageHandlers(self)
        
        self.last_update_id = 0
        
        # Устанавливаем меню команд для обоих языков при инициализации
        self.set_bot_commands_for_all_languages()
    
    def set_bot_commands_for_all_languages(self):
        """Установка меню команд бота для всех доступных языков"""
        available_langs = self.translator.available_languages()
        for lang in available_langs:
            self.set_bot_commands(lang)
    
    def set_bot_commands(self, lang='ru'):
        """Установка меню команд бота на указанном языке"""
        commands = [
            {"command": "start", "description": self.translator.get_message('cmd_start', lang)},
            {"command": "help", "description": self.translator.get_message('cmd_help', lang)},
            {"command": "schedule", "description": self.translator.get_message('cmd_schedule', lang)},
            {"command": "list", "description": self.translator.get_message('cmd_list', lang)},
            {"command": "manage", "description": self.translator.get_message('cmd_manage', lang)},
            {"command": "getchatid", "description": self.translator.get_message('cmd_getchatid', lang)}
        ]
        
        url = f"{self.base_url}/setMyCommands"
        data = {
            "commands": commands,
            "language_code": lang
        }
        
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                logger.info(f"✅ Меню команд бота успешно настроено на языке: {lang}")
            else:
                logger.error(f"❌ Ошибка настройки меню команд: {response.text}")
        except Exception as e:
            logger.error(f"❌ Ошибка при настройке меню команд: {e}")
    
    def _post_json(self, url, data):
        try:
            response = requests.post(url, json=data)
            return response.json()
        except Exception as e:
            logger.error(f"Error sending request to {url}: {e}")
            return None

    def send_message(self, chat_id, text, parse_mode: str = 'Markdown', reply_markup: dict = None):
        """Отправка сообщения в чат.

        `reply_markup` — опциональная структура inline клавиатуры или других
        параметров (как словарь). Возвращает распарсенный JSON ответа Telegram
        или None при ошибке.
        """
        url = f"{self.base_url}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        if reply_markup is not None:
            data['reply_markup'] = reply_markup

        return self._post_json(url, data)
    
    def send_scheduled_message(self, chat_id, message):
        """Отправка запланированного сообщения"""
        logger.info(f"Sending scheduled message to {chat_id}")
        self.send_message(chat_id, message)

    def answer_callback_query(self, callback_query_id, text=None, show_alert=False):
        """Answer a callback query to acknowledge the button press."""
        url = f"{self.base_url}/answerCallbackQuery"
        data = {'callback_query_id': callback_query_id, 'show_alert': show_alert}
        if text:
            data['text'] = text
        return self._post_json(url, data)

    def edit_message_text(self, chat_id, message_id, text, parse_mode='Markdown', reply_markup=None):
        url = f"{self.base_url}/editMessageText"
        data = {'chat_id': chat_id, 'message_id': message_id, 'text': text, 'parse_mode': parse_mode}
        if reply_markup is not None:
            data['reply_markup'] = reply_markup
        return self._post_json(url, data)

    def edit_message_reply_markup(self, chat_id, message_id, reply_markup=None):
        url = f"{self.base_url}/editMessageReplyMarkup"
        data = {'chat_id': chat_id, 'message_id': message_id}
        if reply_markup is not None:
            data['reply_markup'] = reply_markup
        return self._post_json(url, data)
    
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
        # Support both message updates and callback_query updates
        if 'callback_query' in update:
            cq = update['callback_query']
            cq_id = cq['id']
            from_user = cq['from']['id']
            data = cq.get('data')
            message = cq.get('message')
            chat_id = message['chat']['id'] if message and 'chat' in message else None
            message_id = message['message_id'] if message else None
            # Let handlers process callback queries
            self.handlers.handle_callback_query(cq, cq_id, from_user, chat_id, message_id, data)
            return

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