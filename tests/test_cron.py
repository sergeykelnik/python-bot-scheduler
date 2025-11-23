import sys
import os

# Ensure project root is on sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from scheduler import SchedulerManager


class DummyBot:
    def __init__(self):
        pass

    def send_scheduled_message(self, chat_id, message):
        print(f"Would send message to {chat_id}: {message}")


if __name__ == '__main__':
    bot = DummyBot()
    sched = SchedulerManager(bot)
    try:
        result = sched.create_cron_schedule('job_test', '12345', 'Hello', '* * * * *')
        print('create_cron_schedule returned:', result)
        print('Scheduled jobs keys:', list(sched.scheduler.get_jobs()))
    except Exception as e:
        print('create_cron_schedule raised:', e)
