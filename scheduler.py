"""Модуль для работы с планировщиком"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from config import WARSAW_TZ

logger = logging.getLogger(__name__)

class SchedulerManager:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.scheduler = BackgroundScheduler(timezone=WARSAW_TZ)
        self.scheduled_jobs = {}
    
    def load_schedules_from_db(self):
        """Загрузка всех расписаний из базы данных и их восстановление"""
        schedules = self.bot.db.get_all_schedules()
        logger.info(f"Loading {len(schedules)} schedules from database")
        
        for schedule in schedules:
            job_id = schedule['job_id']
            schedule_type = schedule['schedule_type']
            schedule_data = schedule['schedule_data']
            
            try:
                # Добавляем в планировщик только если не на паузе
                if not schedule['is_paused']:
                    if schedule_type == 'daily':
                        self.scheduler.add_job(
                            self.bot.send_scheduled_message,
                            CronTrigger(
                                hour=schedule_data['hour'],
                                minute=schedule_data['minute'],
                                timezone=WARSAW_TZ
                            ),
                            args=[schedule['chat_id'], schedule['message']],
                            id=job_id
                        )
                    
                    elif schedule_type == 'interval':
                        if schedule_data['unit'] == 'hours':
                            trigger = IntervalTrigger(hours=schedule_data['interval'], timezone=WARSAW_TZ)
                        elif schedule_data['unit'] == 'minutes':
                            trigger = IntervalTrigger(minutes=schedule_data['interval'], timezone=WARSAW_TZ)
                        elif schedule_data['unit'] == 'seconds':
                            trigger = IntervalTrigger(seconds=schedule_data['interval'], timezone=WARSAW_TZ)
                        
                        self.scheduler.add_job(
                            self.bot.send_scheduled_message,
                            trigger,
                            args=[schedule['chat_id'], schedule['message']],
                            id=job_id
                        )
                    
                    elif schedule_type == 'cron':
                        self.scheduler.add_job(
                            self.bot.send_scheduled_message,
                            CronTrigger.from_crontab(schedule_data['expression'], timezone=WARSAW_TZ),
                            args=[schedule['chat_id'], schedule['message']],
                            id=job_id
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
    
    def create_daily_schedule(self, job_id, chat_id, message, hour, minute):
        """Создание ежедневного расписания"""
        self.scheduler.add_job(
            self.bot.send_scheduled_message,
            CronTrigger(hour=hour, minute=minute, timezone=WARSAW_TZ),
            args=[chat_id, message],
            id=job_id
        )
        return {'hour': hour, 'minute': minute, 'description': f"Ежедневно в {hour:02d}:{minute:02d} (Europe/Warsaw)"}
    
    def create_interval_schedule(self, job_id, chat_id, message, interval, unit):
        """Создание интервального расписания"""
        if unit == 'hours':
            trigger = IntervalTrigger(hours=interval, timezone=WARSAW_TZ)
            unit_desc = 'час(ов)'
            schedule_unit = 'hours'
        elif unit == 'minutes':
            trigger = IntervalTrigger(minutes=interval, timezone=WARSAW_TZ)
            unit_desc = 'минут(ы)'
            schedule_unit = 'minutes'
        elif unit == 'seconds':
            trigger = IntervalTrigger(seconds=interval, timezone=WARSAW_TZ)
            unit_desc = 'секунд(ы)'
            schedule_unit = 'seconds'
        
        self.scheduler.add_job(
            self.bot.send_scheduled_message,
            trigger,
            args=[chat_id, message],
            id=job_id
        )
        return {'interval': interval, 'unit': schedule_unit, 'description': f"Каждые {interval} {unit_desc} (Europe/Warsaw)"}
    
    def create_cron_schedule(self, job_id, chat_id, message, cron_expression):
        """Создание cron расписания"""
        self.scheduler.add_job(
            self.bot.send_scheduled_message,
            CronTrigger.from_crontab(cron_expression, timezone=WARSAW_TZ),
            args=[chat_id, message],
            id=job_id
        )
        return {'expression': cron_expression, 'description': f"Cron: {cron_expression} (Europe/Warsaw)"}
    
    def pause_job(self, job_id):
        """Приостановка работы"""
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        return True
    
    def resume_job(self, job_id, schedule_type, schedule_data, chat_id, message):
        """Возобновление работы"""
        if schedule_type == 'daily':
            self.create_daily_schedule(job_id, chat_id, message, schedule_data['hour'], schedule_data['minute'])
        elif schedule_type == 'interval':
            self.create_interval_schedule(job_id, chat_id, message, schedule_data['interval'], schedule_data['unit'])
        elif schedule_type == 'cron':
            self.create_cron_schedule(job_id, chat_id, message, schedule_data['expression'])
        return True
    
    def delete_job(self, job_id):
        """Удаление работы из планировщика"""
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        return True
    
    def start(self):
        """Запуск планировщика"""
        self.scheduler.start()
    
    def shutdown(self):
        """Остановка планировщика"""
        self.scheduler.shutdown()