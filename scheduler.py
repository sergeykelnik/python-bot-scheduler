"""Модуль для работы с планировщиком"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from config import WARSAW_TZ

logger = logging.getLogger(__name__)

class SchedulerManager:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.scheduler = BackgroundScheduler(timezone=WARSAW_TZ)
        self.scheduled_jobs = {}
    
    def _validate_cron_expression(self, expression: str) -> bool:
        """
        Validate if a string is a valid cron expression format.
        Must have exactly 5 fields separated by whitespace.
        Supports: numbers, ranges, steps, wildcards, day/month names, and special characters.
        """
        expression = expression.strip()
        parts = expression.split()
        
        # Must have exactly 5 fields
        if len(parts) != 5:
            return False
        
        # Each field must be non-empty
        for field in parts:
            if not field:
                return False
        
        return True
    
    def _add_job_to_scheduler(self, job_id, schedule_data, chat_id, message):
        """Add a cron-based job to the scheduler."""
        # Validate cron expression format before creating trigger
        if not self._validate_cron_expression(schedule_data['expression']):
            raise ValueError(f"Invalid cron format: {schedule_data['expression']}. Must have 5 fields.")
        
        # Convert from standard cron to APScheduler format
        from schedule_manager import ScheduleManager
        schedule_mgr = ScheduleManager()
        converted_expression = schedule_mgr._convert_cron_to_apscheduler_format(schedule_data['expression'])
        
        try:
            trigger = CronTrigger.from_crontab(converted_expression, timezone=WARSAW_TZ)
        except Exception as e:
            raise ValueError(f"Invalid cron expression: {schedule_data['expression']}. Error: {str(e)}")

        self.scheduler.add_job(
            self.bot.send_scheduled_message,
            trigger,
            args=[chat_id, message],
            id=job_id
        )
    
    def load_schedules_from_db(self):
        """Загрузка всех расписаний из базы данных и их восстановление"""
        schedules = self.bot.db.get_schedules()
        logger.info(f"Loading {len(schedules)} schedules from database")
        
        for schedule in schedules:
            job_id = schedule['job_id']
            schedule_data = schedule['schedule_data']
            
            # All schedules should have 'expression' key (cron format)
            if 'expression' not in schedule_data:
                logger.warning(f"Schedule {job_id} missing 'expression' key - skipping")
                continue
            
            try:
                # Добавляем в планировщик только если не на паузе
                if not schedule['is_paused']:
                    self._add_job_to_scheduler(
                        job_id,
                        schedule_data,
                        schedule['chat_id'],
                        schedule['message']
                    )
                
                # Сохраняем в памяти независимо от статуса паузы
                self.scheduled_jobs[job_id] = {
                    'user_id': schedule['user_id'],
                    'chat_id': schedule['chat_id'],
                    'message': schedule['message'],
                    'schedule': schedule_data.get('description', 'Unknown schedule'),
                    'is_paused': schedule['is_paused']
                }
                
                logger.info(f"Loaded schedule: {job_id} (paused: {schedule['is_paused']})")
                
            except Exception as e:
                logger.error(f"Failed to load schedule {job_id}: {e}")
    
    
    def create_cron_schedule(self, job_id, chat_id, message, cron_expression):
        """Создание cron расписания"""
        try:
            schedule_data = {'expression': cron_expression, 'description': f"Cron: {cron_expression} (Europe/Warsaw)"}
            self._add_job_to_scheduler(job_id, schedule_data, chat_id, message)
            return schedule_data
        except Exception as e:
            logger.error(f"Error creating cron schedule: {e}")
            raise
    
    def pause_job(self, job_id):
        """Приостановка работы"""
        try:
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"Job {job_id} paused successfully")
            return True
        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {e}")
            return False
    
    def resume_job(self, job_id, schedule_data, chat_id, message):
        """Возобновление работы"""
        try:
            self._add_job_to_scheduler(job_id, schedule_data, chat_id, message)
            
            logger.info(f"Job {job_id} resumed successfully")
            return True
        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {e}")
            return False
    
    def delete_job(self, job_id):
        """Удаление работы из планировщика"""
        try:
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            return True
        except Exception as e:
            logger.error(f"Error deleting job {job_id}: {e}")
            return False
    
    def start(self):
        """Запуск планировщика"""
        self.scheduler.start()
    
    def shutdown(self):
        """Остановка планировщика"""
        self.scheduler.shutdown()