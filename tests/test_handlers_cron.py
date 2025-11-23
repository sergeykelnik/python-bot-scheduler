import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from scheduler import SchedulerManager
from database import Database
from handlers import MessageHandlers

class DummyBot:
    def __init__(self):
        self.db = Database()
        self.scheduler = SchedulerManager(self)
    def send_scheduled_message(self, chat_id, message):
        print('scheduled send', chat_id, message)
    def send_message_with_markup(self, chat_id, text, reply_markup=None, parse_mode='Markdown'):
        print('send_message_with_markup:', chat_id, text)
    def send_message(self, chat_id, text):
        print('send_message:', chat_id, text)

if __name__ == '__main__':
    bot = DummyBot()
    handler = MessageHandlers(bot)
    state={'chat_id': '12345', 'message':'Hello cron'}
    handler.create_schedule('12345', 999, '* * * * *', state)
