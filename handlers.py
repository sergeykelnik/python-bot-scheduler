"""Обработчики сообщений и команд"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Глобальные состояния пользователей
user_states = {}

class MessageHandlers:
    def __init__(self, bot_instance):
        self.bot = bot_instance
    
    def handle_start(self, chat_id, user_id):
        """Обработка команды /start"""
        text = (
            "🤖 *Бот планирования сообщений*\n\n"
            "Команды:\n"
            "/schedule - Создать новое расписание\n"
            "/list - Показать активные расписания\n"
            "/manage - Управление расписаниями (удалить, приостановить, возобновить)\n"
            "/getchatid - Получить ID текущего чата\n"
            "/help - Подробная помощь"
        )
        self.bot.send_message(chat_id, text)
    
    def handle_help(self, chat_id, user_id):
        """Обработка команды /help"""
        text = """
🤖 *Помощь по боту планировщику сообщений*

*Создание расписаний:*
1. Введите команду /schedule
2. Введите целевой chat ID (или используйте 'me')
3. Введите сообщение
4. Выберите тип расписания:
   • Ежедневно: `daily HH:MM` (например, `daily 09:00`)
   • Интервал: `every X hours/minutes/seconds` (например, `every 2 hours`)
   • Cron: используйте cron-формат (например, `0 9 * * MON`)

*Примеры:*
• `daily 09:00` - Каждый день в 9:00
• `every 30 minutes` - Каждые 30 минут
• `every 2 hours` - Каждые 2 часа
• `0 9 * * MON` - Каждый понедельник в 9:00

*Управление расписаниями:*
• /list - Показать все расписания
• /manage - Интерактивное управление (удалить, приостановить, возобновить)

*Команды:*
/schedule - Запустить мастер создания расписания
/list - Показать все активные расписания
/manage - Управление расписаниями
/getchatid - Получить ID текущего чата
        """
        self.bot.send_message(chat_id, text)
    
    def handle_schedule(self, chat_id, user_id):
        """Обработка команды /schedule"""
        user_states[user_id] = {'step': 'chat_id'}
        text = (
            "📝 Давайте создадим расписание!\n\n"
            "Шаг 1: Введите целевой chat ID\n"
            "(Используйте 'me', чтобы отправить себе, или укажите chat ID)\n\n"
            "Подсказка: используйте /getchatid, чтобы узнать ID чата"
        )
        self.bot.send_message(chat_id, text)
    
    def handle_list(self, chat_id, user_id):
        """Обработка команды /list"""
        user_jobs = {k: v for k, v in self.bot.scheduler.scheduled_jobs.items() 
                     if v['user_id'] == user_id}
        
        if not user_jobs:
            self.bot.send_message(chat_id, "У вас нет активных расписаний.")
            return
        
        text = "📋 *Ваши активные расписания:*\n\n"
        for job_id, job_info in user_jobs.items():
            status = "⏸️ ПРИОСТАНОВЛЕНО" if job_info['is_paused'] else "✅ АКТИВНО"
            text += f"ID: `{job_id}`\n"
            text += f"Статус: {status}\n"
            text += f"Цель: {job_info['chat_id']}\n"
            text += f"Сообщение: {job_info['message'][:50]}...\n"
            text += f"Расписание: {job_info['schedule']}\n"
            text += f"─────────────\n"
        
        text += "\nИспользуйте /manage для управления расписаниями"
        self.bot.send_message(chat_id, text)
    
    def handle_manage(self, chat_id, user_id):
        """Обработка команды /manage - показать интерактивный список"""
        user_jobs = {k: v for k, v in self.bot.scheduler.scheduled_jobs.items() 
                     if v['user_id'] == user_id}
        
        if not user_jobs:
            self.bot.send_message(chat_id, "У вас нет расписаний для управления.")
            return
        
        # Сохраняем jobs для этой сессии управления
        user_states[user_id] = {
            'step': 'manage_select',
            'management_jobs': list(user_jobs.keys())
        }
        
        text = "🛠️ *Управление расписаниями*\n\nВыберите расписание:\n\n"
        
        for i, job_id in enumerate(user_jobs.keys(), 1):
            job_info = user_jobs[job_id]
            status = "⏸️ ПРИОСТАНОВЛЕНО" if job_info['is_paused'] else "✅ АКТИВНО"
            text += f"{i}. `{job_id}`\n"
            text += f"   Статус: {status}\n"
            text += f"   Сообщение: {job_info['message'][:30]}...\n"
            text += f"   Расписание: {job_info['schedule']}\n\n"
        
        text += "Введите номер расписания для управления:"
        self.bot.send_message(chat_id, text)
    
    def handle_manage_selection(self, chat_id, user_id, selection):
        """Обработка выбора работы в режиме управления"""
        try:
            job_index = int(selection) - 1
            management_jobs = user_states[user_id]['management_jobs']
            
            if 0 <= job_index < len(management_jobs):
                job_id = management_jobs[job_index]
                job_info = self.bot.scheduler.scheduled_jobs[job_id]
                
                # Сохраняем выбранную работу для действия
                user_states[user_id] = {
                    'step': 'manage_action',
                    'selected_job': job_id
                }
                
                status = "⏸️ ПРИОСТАНОВЛЕНО" if job_info['is_paused'] else "✅ АКТИВНО"
                pause_resume_text = "⏸️ Приостановить" if not job_info['is_paused'] else "▶️ Возобновить"
                
                text = f"🛠️ *Управление расписанием:*\n\n"
                text += f"ID: `{job_id}`\n"
                text += f"Статус: {status}\n"
                text += f"Цель: {job_info['chat_id']}\n"
                text += f"Сообщение: {job_info['message']}\n"
                text += f"Расписание: {job_info['schedule']}\n\n"
                text += f"Выберите действие:\n"
                text += f"1. 🗑️ Удалить\n"
                text += f"2. {pause_resume_text}\n"
                text += f"3. ↩️ Назад к списку"
                
                self.bot.send_message(chat_id, text)
            else:
                self.bot.send_message(chat_id, "❌ Неверный номер. Пожалуйста, выберите номер из списка.")
        except ValueError:
            self.bot.send_message(chat_id, "❌ Пожалуйста, введите номер расписания.")
    
    def handle_manage_action(self, chat_id, user_id, action):
        """Обработка выбора действия в режиме управления"""
        job_id = user_states[user_id]['selected_job']
        
        if action == '1':  # Удалить
            self.delete_job(chat_id, user_id, job_id)
            del user_states[user_id]
        
        elif action == '2':  # Пауза/Возобновить
            self.toggle_job_pause(chat_id, user_id, job_id)
            # Возвращаемся к списку управления
            self.handle_manage(chat_id, user_id)
        
        elif action == '3':  # Назад к списку
            self.handle_manage(chat_id, user_id)
        
        else:
            self.bot.send_message(chat_id, "❌ Неверное действие. Пожалуйста, выберите 1, 2 или 3.")
    
    def handle_getchatid(self, chat_id, user_id):
        """Обработка команды /getchatid"""
        self.bot.send_message(chat_id, f"ID этого чата: `{chat_id}`")
    
    def handle_text_message(self, chat_id, user_id, text):
        """Обработка текстовых сообщений для мастера планирования и управления"""
        if user_id not in user_states:
            return
        
        state = user_states[user_id]
        step = state['step']
        
        if step == 'chat_id':
            target_chat = text if text.lower() != 'me' else chat_id
            state['chat_id'] = target_chat
            state['step'] = 'message'
            self.bot.send_message(chat_id, "Шаг 2: Введите сообщение, которое хотите отправить:")
        
        elif step == 'message':
            state['message'] = text
            state['step'] = 'schedule'
            self.bot.send_message(
                chat_id,
                "Шаг 3: Выберите тип расписания:\n\n"
                "Примеры:\n"
                "• `daily 09:00` - Ежедневно в 09:00\n"
                "• `every 30 minutes` - Каждые 30 минут\n"
                "• `every 2 hours` - Каждые 2 часа\n"
                "• `0 9 * * MON` - Каждый понедельник в 09:00 (cron)\n\n"
                "Введите ваше расписание:"
            )
        
        elif step == 'schedule':
            self.create_schedule(chat_id, user_id, text, state)
        
        elif step == 'manage_select':
            self.handle_manage_selection(chat_id, user_id, text)
        
        elif step == 'manage_action':
            self.handle_manage_action(chat_id, user_id, text)
    
    def create_schedule(self, chat_id, user_id, schedule_text, state):
        """Создание нового расписания"""
        job_id = f"job_{user_id}_{int(datetime.now().timestamp())}"
        
        try:
            schedule_text = schedule_text.strip()
            schedule_data = {}
            schedule_type = ""
            
            # Парсинг ежедневного расписания
            if schedule_text.startswith('daily'):
                parts = schedule_text.split()
                if len(parts) < 2:
                    raise ValueError("Format: daily HH:MM")
                time_str = parts[1]
                hour, minute = map(int, time_str.split(':'))
                
                schedule_data = self.bot.scheduler.create_daily_schedule(job_id, state['chat_id'], state['message'], hour, minute)
                schedule_type = 'daily'
            
            # Парсинг интервального расписания
            elif schedule_text.startswith('every'):
                parts = schedule_text.split()
                if len(parts) < 2:
                    raise ValueError("Format: every X hours/minutes")
                
                interval = int(parts[1])
                unit = parts[2] if len(parts) > 2 else 'hours'
                
                # Нормализация единицы измерения
                if unit.startswith('hour'):
                    schedule_unit = 'hours'
                elif unit.startswith('minute'):
                    schedule_unit = 'minutes'
                elif unit.startswith('second'):
                    schedule_unit = 'seconds'
                else:
                    raise ValueError("Unit must be hours, minutes, or seconds")
                
                schedule_data = self.bot.scheduler.create_interval_schedule(job_id, state['chat_id'], state['message'], interval, schedule_unit)
                schedule_type = 'interval'
            
            # Парсинг cron выражения
            else:
                schedule_data = self.bot.scheduler.create_cron_schedule(job_id, state['chat_id'], state['message'], schedule_text)
                schedule_type = 'cron'
            
            # Сохраняем информацию о работе в памяти
            self.bot.scheduler.scheduled_jobs[job_id] = {
                'user_id': user_id,
                'chat_id': state['chat_id'],
                'message': state['message'],
                'schedule': schedule_data['description'],
                'is_paused': False
            }
            
            # Сохраняем в базу данных
            self.bot.db.save_schedule(
                job_id=job_id,
                user_id=user_id,
                chat_id=state['chat_id'],
                message=state['message'],
                schedule_type=schedule_type,
                schedule_data=schedule_data,
                is_paused=False
            )
            
            self.bot.send_message(
                chat_id,
                f"✅ *Расписание успешно создано!*\n\n"
                f"ID: `{job_id}`\n"
                f"Расписание: {schedule_data['description']}\n"
                f"Цель: {state['chat_id']}\n\n"
                f"Используйте /list, чтобы увидеть все расписания\n"
                f"Используйте /manage для управления расписаниями"
            )
            
            # Очищаем состояние пользователя
            del user_states[user_id]
            
        except Exception as e:
            self.bot.send_message(chat_id, f"❌ Ошибка при создании расписания: {e}\n\nПожалуйста, попробуйте снова с /schedule")
            del user_states[user_id]
    
    def delete_job(self, chat_id, user_id, job_id):
        """Удаление работы полностью"""
        try:
            if job_id in self.bot.scheduler.scheduled_jobs and self.bot.scheduler.scheduled_jobs[job_id]['user_id'] == user_id:
                # Удаляем из планировщика
                self.bot.scheduler.delete_job(job_id)
                
                # Удаляем из базы данных
                self.bot.db.delete_schedule(job_id)
                
                # Удаляем из памяти
                del self.bot.scheduler.scheduled_jobs[job_id]
                
                self.bot.send_message(chat_id, f"✅ Расписание `{job_id}` успешно удалено!")
            else:
                self.bot.send_message(chat_id, "❌ Расписание не найдено или у вас нет прав.")
        except Exception as e:
            self.bot.send_message(chat_id, f"❌ Ошибка при удалении расписания: {e}")
    
    def toggle_job_pause(self, chat_id, user_id, job_id):
        """Приостановка или возобновление работы"""
        try:
            if job_id in self.bot.scheduler.scheduled_jobs and self.bot.scheduler.scheduled_jobs[job_id]['user_id'] == user_id:
                job_info = self.bot.scheduler.scheduled_jobs[job_id]
                is_paused = job_info['is_paused']
                
                if is_paused:
                    # Возобновляем работу - воссоздаем в планировщике
                    db_schedule = next((s for s in self.bot.db.get_user_schedules(user_id) if s['job_id'] == job_id), None)
                    if db_schedule:
                        self.bot.scheduler.resume_job(
                            job_id, 
                            db_schedule['schedule_type'], 
                            db_schedule['schedule_data'],
                            job_info['chat_id'],
                            job_info['message']
                        )
                        
                        # Обновляем в памяти и базе данных
                        self.bot.scheduler.scheduled_jobs[job_id]['is_paused'] = False
                        self.bot.db.update_schedule_pause_status(job_id, False)
                        
                        self.bot.send_message(chat_id, f"▶️ Расписание `{job_id}` возобновлено!")
                    else:
                        self.bot.send_message(chat_id, "❌ Ошибка: расписание не найдено в базе данных.")
                
                else:
                    # Приостанавливаем работу - удаляем из планировщика но оставляем в памяти и базе данных
                    self.bot.scheduler.pause_job(job_id)
                    
                    # Обновляем в памяти и базе данных
                    self.bot.scheduler.scheduled_jobs[job_id]['is_paused'] = True
                    self.bot.db.update_schedule_pause_status(job_id, True)
                    
                    self.bot.send_message(chat_id, f"⏸️ Расписание `{job_id}` приостановлено!")
            else:
                self.bot.send_message(chat_id, "❌ Расписание не найдено или у вас нет прав.")
        except Exception as e:
            self.bot.send_message(chat_id, f"❌ Ошибка при изменении статуса расписания: {e}")