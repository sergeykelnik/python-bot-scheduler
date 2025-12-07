"""
Telegram Bot Main Class.
"""

import logging
import time
import requests
from typing import Optional, Dict

from src.core.config import BOT_TOKEN, LOG_FORMAT, LOG_LEVEL
from src.core.database import Database
from src.services.translation_service import TranslationService
from src.services.scheduler_service import SchedulerService
from src.services.ai_service import AIService
from src.bot.handlers import MessageHandlers

# Setup logging
logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
logger = logging.getLogger(__name__)

class TelegramBot:
    """Main Bot Class handling initialization and updates polling."""
    
    def __init__(self, token: str):
        """
        Initialize the bot.
        
        Args:
            token: Telegram Bot Token.
        """
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.last_update_id = 0
        
        # Initialize Components
        logger.info("Initializing bot components...")
        self.translator = TranslationService()
        self.db = Database()
        self.ai_service = AIService()
        
        # Scheduler needs a callback to send messages
        self.scheduler = SchedulerService(callback_func=self.send_scheduled_message)
        
        # Handlers need access to bot instance to reply
        self.handlers = MessageHandlers(self)
        
        # Set commands for all languages on startup
        self.set_bot_commands_for_all_languages()
        
    def set_bot_commands_for_all_languages(self):
        """Set bot menu commands for all available languages."""
        available_langs = self.translator.available_languages()
        for lang in available_langs:
            self.set_bot_commands(lang)
            
    def set_bot_commands(self, lang: str = 'ru'):
        """
        Set bot menu commands for a specific language.
        
        Args:
            lang: Language code.
        """
        commands = [
            {"command": "start", "description": self.translator.get_message('cmd_start', lang)},
            {"command": "help", "description": self.translator.get_message('cmd_help', lang)},
            {"command": "schedule", "description": self.translator.get_message('cmd_schedule', lang)},
            {"command": "list", "description": self.translator.get_message('cmd_list', lang)},
            {"command": "manage", "description": self.translator.get_message('cmd_manage', lang)}
        ]
        
        url = f"{self.base_url}/setMyCommands"
        data = {
            "commands": commands,
            "language_code": lang
        }
        
        try:
            self._post_json(url, data)
            logger.debug(f"Bot commands set for language: {lang}")
        except Exception as e:
            logger.error(f"Error setting bot commands for {lang}: {e}")

    def _post_json(self, url: str, data: Dict) -> Optional[Dict]:
        """Helper to send POST request with JSON data."""
        try:
            response = requests.post(url, json=data)
            return response.json()
        except Exception as e:
            logger.error(f"Error sending request to {url}: {e}")
            return None
            
    def send_message(self, chat_id: str, text: str, parse_mode: str = 'Markdown', reply_markup: Dict = None):
        """
        Send a text message to a chat.
        
        Args:
            chat_id: Target chat ID.
            text: Message text.
            parse_mode: Parsing mode (default 'Markdown').
            reply_markup: Inline keyboard or other markup.
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

    def send_scheduled_message(self, chat_id: str, message: str):
        """Callback for scheduler to send messages."""
        logger.info(f"Sending scheduled message to {chat_id}")
        self.send_message(chat_id, message)

    def answer_callback_query(self, callback_query_id: str, text: Optional[str] = None, show_alert: bool = False):
        """Answer a callback query."""
        url = f"{self.base_url}/answerCallbackQuery"
        data = {'callback_query_id': callback_query_id, 'show_alert': show_alert}
        if text:
            data['text'] = text
        return self._post_json(url, data)

    def edit_message_text(self, chat_id: str, message_id: int, text: str, parse_mode: str = 'Markdown', reply_markup: Dict = None):
        """Edit an existing message text."""
        url = f"{self.base_url}/editMessageText"
        data = {'chat_id': chat_id, 'message_id': message_id, 'text': text, 'parse_mode': parse_mode}
        if reply_markup is not None:
            data['reply_markup'] = reply_markup
        return self._post_json(url, data)

    def get_updates(self, offset: Optional[int] = None, timeout: int = 30):
        """Get updates from Telegram."""
        url = f"{self.base_url}/getUpdates"
        params = {'timeout': timeout, 'offset': offset}
        try:
            response = requests.get(url, params=params, timeout=timeout+5)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting updates: {e}")
            return None

    def process_update(self, update: Dict):
        """Process a single update."""
        # Handle Callback Queries
        if 'callback_query' in update:
            cq = update['callback_query']
            cq_id = cq['id']
            from_user = cq['from']['id']
            data = cq.get('data')
            message = cq.get('message')
            chat_id = message['chat']['id'] if message and 'chat' in message else None
            message_id = message['message_id'] if message else None
            
            self.handlers.handle_callback_query(cq, cq_id, from_user, chat_id, message_id, data)
            return

        # Handle Messages
        if 'message' in update:
            message = update['message']
            if 'text' not in message:
                return
                
            chat_id = message['chat']['id']
            user_id = message['from']['id']
            text = message['text']

            # Commands
            if text.startswith('/'):
                command_parts = text.split()
                command = command_parts[0].split('@')[0]
                
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
                self.handlers.handle_text_message(chat_id, user_id, text)

    def load_existing_schedules(self):
        """Load schedules from DB into memory on startup."""
        schedules = self.db.get_schedules()
        logger.info(f"Loading {len(schedules)} schedules from database...")
        for s in schedules:
            if not s['is_paused']:
                try:
                    self.scheduler.add_job(
                        s['job_id'], 
                        s['chat_id'], 
                        s['message'], 
                        s['schedule_data']['expression']
                    )
                except Exception as e:
                    logger.error(f"Failed to restore job {s['job_id']}: {e}")

    def start_polling(self):
        """Start the bot."""
        logger.info("Bot started! Press Ctrl+C to stop.")
        
        # Load and Start Scheduler
        self.load_existing_schedules()
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
