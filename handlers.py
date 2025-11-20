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
            "Выберите действие ниже или используйте команды в чате."
        )
        markup = {
            'inline_keyboard': [
                [
                    {'text': '📅 Создать', 'callback_data': 'cmd:schedule'},
                    {'text': '📋 Мои расписания', 'callback_data': 'cmd:list'}
                ],
                [
                    {'text': '⚙️ Управление', 'callback_data': 'cmd:manage'},
                    {'text': '🆔 Получить ID', 'callback_data': 'cmd:getchatid'}
                ],
                [
                    {'text': '📖 Помощь', 'callback_data': 'cmd:help'}
                ]
            ]
        }
        self.bot.send_message_with_markup(chat_id, text, reply_markup=markup, parse_mode='Markdown')
    
    def handle_help(self, chat_id, user_id):
        """Обработка команды /help"""
        text = (
            "🤖 *Помощь по боту планировщику сообщений*\n\n"
            "*Создание расписаний:*\n"
            "1. Введите команду /schedule\n"
            "2. Введите 'me' (или укажите chat ID получателя)\n"
            "3. Введите сообщение\n"
            "4. Выберите тип расписания\n"
            "5. Все расписания работают по Центральноевропейскому времени\n\n"
            "*Примеры простых расписаний:*\n"
            "`daily 09:00` - Каждый день в 09:00\n"
            "`daily 14:35` - Каждый день в 14:35\n"
            "`every 30 minutes` - Каждые 30 минут\n"
            "`every 2 hours` - Каждые 2 часа\n"
            "`every 10 seconds` - Каждые 10 секунд (удобно для тестирования)\n\n"
            "*Примеры в формате Cron:*\n"
            "`0 9 * * MON` - Каждый понедельник в 09:00\n"
            "`0 8 * * MON-FRI` - Каждый будний день в 08:00\n"
            "`0 0 1 * *` - Первого числа каждого месяца в 00:00\n"
            "`30 6 15 * *` - 15 числа каждого месяца в 06:30\n"
            "`*/15 * * * *` - Каждые 15 минут\n\n"
            "*Команды:*\n"
            "/schedule - Запустить мастер создания расписания\n"
            "/list - Показать все активные расписания\n"
            "/manage - Управление расписаниями\n"
            "/getchatid - Получить ID текущего чата\n"
            "/help - Показать эту справку\n\n"
            "Подсказка: для сложных cron-выражений используйте генераторы, например http://www.cronmaker.com/."
        )
        
        # Добавим быстрые кнопки команд внизу помощи
        markup = {'inline_keyboard': [[
            {'text': '📅 Создать', 'callback_data': 'cmd:schedule'},
            {'text': '📋 Мои расписания', 'callback_data': 'cmd:list'},
            {'text': '⚙️ Управление', 'callback_data': 'cmd:manage'}
        ]]}
        self.bot.send_message_with_markup(chat_id, text, reply_markup=markup, parse_mode='Markdown')
    
    def handle_schedule(self, chat_id, user_id):
        """Обработка команды /schedule"""
        user_states[user_id] = {'step': 'chat_id'}
        text = (
            "📝 Давайте создадим расписание!\n\n"
            "Шаг 1: Введите целевой chat ID\n"
            "(Используйте 'me', чтобы отправить себе, или укажите chat ID)"
        )
        # Добавим кнопку получения chat_id и кнопку 'me' для отправки себе
        markup = {'inline_keyboard': [[
            {'text': '🆔 Получить ID чата', 'callback_data': 'cmd:getchatid'},
            {'text': '👤 Мне (me)', 'callback_data': 'schedule:me'}
        ]]}
        self.bot.send_message_with_markup(chat_id, text, reply_markup=markup, parse_mode='Markdown')
    
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
        # Добавим кнопку управления после списка
        markup = {'inline_keyboard': [[{'text': '⚙️ Управление', 'callback_data': 'cmd:manage'}]]}
        self.bot.send_message_with_markup(chat_id, text, reply_markup=markup, parse_mode='Markdown')
    
    def handle_manage(self, chat_id, user_id):
        """Обработка команды /manage - показать интерактивный список"""
        user_jobs = {k: v for k, v in self.bot.scheduler.scheduled_jobs.items() if v['user_id'] == user_id}

        if not user_jobs:
            self.bot.send_message(chat_id, "У вас нет расписаний для управления.")
            return

        # Для каждого расписания отправляем отдельное сообщение с inline-кнопками
        for job_id, job_info in user_jobs.items():
            text = self._build_job_text(job_id, job_info)
            markup = self._build_job_markup(job_id, job_info)
            # send a separate message per job with inline buttons
            self.bot.send_message_with_markup(chat_id, text, reply_markup=markup, parse_mode='Markdown')
    
    def handle_manage_selection(self, chat_id, user_id, selection):
        """(Устаревший) выбор работы больше не используется."""
    
    def handle_manage_action(self, chat_id, user_id, action):
        """(Устаревший) действие управления через ввод номера не поддерживается."""
    
    def handle_getchatid(self, chat_id, user_id):
        """Обработка команды /getchatid"""
        self.bot.send_message(chat_id, f"ID этого чата: `{chat_id}`")

    # --- Helpers for interactive manage ---
    def _build_job_text(self, job_id, job_info):
        status = "⏸️ ПРИОСТАНОВЛЕНО" if job_info.get('is_paused') else "✅ АКТИВНО"
        text = (
            f"*ID:* `{job_id}`\n"
            f"*Статус:* {status}\n"
            f"*Цель:* {job_info.get('chat_id')}\n"
            f"*Сообщение:* {job_info.get('message')}\n"
            f"*Расписание:* {job_info.get('schedule')}\n"
        )
        return text

    def _build_job_markup(self, job_id, job_info):
        # Return inline keyboard depending on paused status
        if job_info.get('is_paused'):
            buttons = [
                {'text': '▶️ Возобновить', 'callback_data': f'manage:resume:{job_id}'},
                {'text': '🗑️ Удалить', 'callback_data': f'manage:delete:{job_id}'}
            ]
        else:
            buttons = [
                {'text': '⏸️ Приостановить', 'callback_data': f'manage:pause:{job_id}'},
                {'text': '🗑️ Удалить', 'callback_data': f'manage:delete:{job_id}'}
            ]

        # Inline keyboard uses rows; put two buttons on one row
        return {'inline_keyboard': [buttons]}

    def handle_callback_query(self, cq, cq_id, from_user, chat_id, message_id, data):
        """Обработка callback_query от inline-кнопок управления.

        data examples:
        - 'manage:pause:<job_id>'
        - 'manage:resume:<job_id>'
        - 'manage:delete:<job_id>' (will ask confirmation by editing the same message)
        - 'confirm_delete:<job_id>'
        - 'cancel_delete:<job_id>'
        """
        try:
            if not data:
                self.bot.answer_callback_query(cq_id)
                return

            parts = data.split(':')
            action = parts[0]

            # Quick schedule actions (e.g. send to 'me')
            if action == 'schedule' and len(parts) >= 2:
                sub = parts[1]
                # set the user's target chat to the current chat (me)
                if sub == 'me':
                    # initialize or update state to step 'message'
                    user_states[from_user] = {'step': 'message', 'chat_id': chat_id}
                    # acknowledge and prompt for message text
                    self.bot.answer_callback_query(cq_id)
                    self.bot.send_message(chat_id, "Шаг 2: Введите сообщение, которое хотите отправить:")
                    return

            # Generic command buttons (from main menu/help etc.)
            if action == 'cmd' and len(parts) >= 2:
                cmd = parts[1]
                # acknowledge button press
                self.bot.answer_callback_query(cq_id)
                if cmd == 'schedule':
                    self.handle_schedule(chat_id, from_user)
                elif cmd == 'list':
                    self.handle_list(chat_id, from_user)
                elif cmd == 'manage':
                    self.handle_manage(chat_id, from_user)
                elif cmd == 'getchatid':
                    self.handle_getchatid(chat_id, from_user)
                elif cmd == 'help':
                    self.handle_help(chat_id, from_user)
                else:
                    # unknown command
                    self.bot.answer_callback_query(cq_id)
                return

            if action == 'manage' and len(parts) == 3:
                subaction, job_id = parts[1], parts[2]

                # Permission check
                job = self.bot.scheduler.scheduled_jobs.get(job_id)
                if not job:
                    self.bot.answer_callback_query(cq_id, text='Расписание не найдено', show_alert=True)
                    return
                if job.get('user_id') != from_user:
                    self.bot.answer_callback_query(cq_id, text='У вас нет прав для этого действия', show_alert=True)
                    return

                if subaction == 'pause':
                    success = self.bot.scheduler.pause_job(job_id)
                    if success:
                        job['is_paused'] = True
                        self.bot.db.update_schedule_pause_status(job_id, True)
                        new_text = self._build_job_text(job_id, job)
                        new_markup = self._build_job_markup(job_id, job)
                        self.bot.edit_message_text(chat_id, message_id, new_text, parse_mode='Markdown', reply_markup=new_markup)
                        self.bot.answer_callback_query(cq_id, text='Расписание приостановлено')
                    else:
                        self.bot.answer_callback_query(cq_id, text='Ошибка при приостановке', show_alert=True)

                elif subaction == 'resume':
                    # Load schedule data from DB
                    schedules = self.bot.db.get_user_schedules(from_user)
                    target = None
                    for s in schedules:
                        if s['job_id'] == job_id:
                            target = s
                            break
                    if not target:
                        self.bot.answer_callback_query(cq_id, text='Расписание не найдено в базе', show_alert=True)
                        return
                    success = self.bot.scheduler.resume_job(job_id, target['schedule_type'], target['schedule_data'], target['chat_id'], target['message'])
                    if success:
                        job['is_paused'] = False
                        self.bot.db.update_schedule_pause_status(job_id, False)
                        new_text = self._build_job_text(job_id, job)
                        new_markup = self._build_job_markup(job_id, job)
                        self.bot.edit_message_text(chat_id, message_id, new_text, parse_mode='Markdown', reply_markup=new_markup)
                        self.bot.answer_callback_query(cq_id, text='Расписание возобновлено')
                    else:
                        self.bot.answer_callback_query(cq_id, text='Ошибка при возобновлении', show_alert=True)

                elif subaction == 'delete':
                    # Edit the same message to ask for confirmation
                    confirm_text = f"⚠️ Подтвердите удаление расписания `{job_id}`\n\n" + self._build_job_text(job_id, job)
                    confirm_markup = {'inline_keyboard': [[
                        {'text': '✅ Подтвердить удаление', 'callback_data': f'confirm_delete:{job_id}'},
                        {'text': '❌ Отмена', 'callback_data': f'cancel_delete:{job_id}'}
                    ]]}
                    self.bot.edit_message_text(chat_id, message_id, confirm_text, parse_mode='Markdown', reply_markup=confirm_markup)
                    self.bot.answer_callback_query(cq_id)
                else:
                    self.bot.answer_callback_query(cq_id)

            elif action == 'confirm_delete' and len(parts) == 2:
                job_id = parts[1]
                job = self.bot.scheduler.scheduled_jobs.get(job_id)
                if not job:
                    self.bot.answer_callback_query(cq_id, text='Расписание не найдено', show_alert=True)
                    return
                if job.get('user_id') != from_user:
                    self.bot.answer_callback_query(cq_id, text='У вас нет прав для этого действия', show_alert=True)
                    return

                # Proceed to delete
                self.bot.scheduler.delete_job(job_id)
                self.bot.db.delete_schedule(job_id)
                # remove from memory
                del self.bot.scheduler.scheduled_jobs[job_id]
                # Edit message to indicate deletion
                del_text = f"✅ Расписание `{job_id}` удалено"
                self.bot.edit_message_text(chat_id, message_id, del_text, parse_mode='Markdown', reply_markup={})
                self.bot.answer_callback_query(cq_id, text='Расписание удалено')

            elif action == 'cancel_delete' and len(parts) == 2:
                job_id = parts[1]
                job = self.bot.scheduler.scheduled_jobs.get(job_id)
                if not job:
                    self.bot.answer_callback_query(cq_id, text='Расписание не найдено', show_alert=True)
                    return
                # restore original message and buttons
                orig_text = self._build_job_text(job_id, job)
                orig_markup = self._build_job_markup(job_id, job)
                self.bot.edit_message_text(chat_id, message_id, orig_text, parse_mode='Markdown', reply_markup=orig_markup)
                self.bot.answer_callback_query(cq_id, text='Отменено')

            else:
                # Unknown action
                self.bot.answer_callback_query(cq_id)

        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
            try:
                self.bot.answer_callback_query(cq_id, text='Внутренняя ошибка', show_alert=True)
            except Exception:
                pass
    
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
                "`daily 09:00` - Ежедневно в 09:00\n"
                "`every 30 minutes` - Каждые 30 минут\n"
                "`every 2 hours` - Каждые 2 часа\n"
                "`0 9 * * MON` - Каждый понедельник в 09:00 (cron)\n\n"
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
            schedule_text = schedule_text.strip()
            schedule_text_lower = schedule_text.lower()

            if schedule_text_lower.startswith('daily'):
                parts = schedule_text.split()
                if len(parts) < 2:
                    raise ValueError("Формат: daily HH:MM (например: daily 09:00)")
                time_str = parts[1]

                # Проверка формата времени
                if ':' not in time_str:
                    raise ValueError("Неверный формат времени. Используйте HH:MM")

                hour, minute = map(int, time_str.split(':'))

                # Проверка валидности времени
                if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                    raise ValueError("Неверное время. Часы должны быть от 0 до 23, минуты от 0 до 59")

                schedule_data = self.bot.scheduler.create_daily_schedule(job_id, state['chat_id'], state['message'], hour, minute)
                schedule_type = 'daily'

            # Парсинг интервального расписания
            elif schedule_text_lower.startswith('every'):
                parts = schedule_text.split()
                if len(parts) < 3:
                    raise ValueError("Формат: every X hours/minutes/seconds (например: every 10 seconds)")

                try:
                    interval = int(parts[1])
                except ValueError:
                    raise ValueError("Интервал должен быть числом (например: every 10 seconds)")

                if interval <= 0:
                    raise ValueError("Интервал должен быть положительным числом")

                unit = parts[2].lower()

                # Нормализация единицы измерения
                if unit.startswith('hour'):
                    schedule_unit = 'hours'
                elif unit.startswith('minute'):
                    schedule_unit = 'minutes'
                elif unit.startswith('second'):
                    schedule_unit = 'seconds'
                else:
                    raise ValueError("Единица измерения должна быть: hours, minutes или seconds")

                schedule_data = self.bot.scheduler.create_interval_schedule(job_id, state['chat_id'], state['message'], interval, schedule_unit)
                schedule_type = 'interval'

            # Парсинг cron выражения
            else:
                # Базовая проверка cron выражения
                cron_parts = schedule_text.split()
                if len(cron_parts) != 5:
                    raise ValueError("Cron выражение должно содержать 5 частей (например: 0 9 * * MON)")

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
            
            # Send success message with quick action buttons
            success_text = (
                f"✅ *Расписание успешно создано!*\n\n"
                f"ID: `{job_id}`\n"
                f"Расписание: {schedule_data['description']}\n"
                f"Цель: {state['chat_id']}\n"
            )
            success_markup = {'inline_keyboard': [
                [
                    {'text': '📋 Мои расписания', 'callback_data': 'cmd:list'},
                    {'text': '⚙️ Управление', 'callback_data': 'cmd:manage'}
                ],
                [
                    {'text': '🗑️ Отменить это расписание', 'callback_data': f'manage:delete:{job_id}'}
                ]
            ]}
            self.bot.send_message_with_markup(chat_id, success_text, reply_markup=success_markup, parse_mode='Markdown')
            
            # Очищаем состояние пользователя
            del user_states[user_id]
            
        except Exception as e:
            error_message = f"❌ Ошибка при создании расписания: {e}\n\nПожалуйста, попробуйте снова с /schedule"
            self.bot.send_message(chat_id, error_message)
            logger.error(f"Error creating schedule: {e}")
            
            # Очищаем состояние пользователя при ошибке
            if user_id in user_states:
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
                    db_schedule = self.bot.db.get_user_schedules(user_id)
                    if not db_schedule:
                        self.bot.send_message(chat_id, "❌ Ошибка: у вас нет расписаний в базе данных.")
                        return
                    
                    # Ищем конкретное расписание
                    target_schedule = None
                    for schedule in db_schedule:
                        if schedule['job_id'] == job_id:
                            target_schedule = schedule
                            break
                    
                    if not target_schedule:
                        self.bot.send_message(chat_id, "❌ Ошибка: расписание не найдено в базе данных.")
                        return
                    
                    # Восстанавливаем работу в планировщике
                    success = self.bot.scheduler.resume_job(
                        job_id, 
                        target_schedule['schedule_type'], 
                        target_schedule['schedule_data'],
                        job_info['chat_id'],
                        job_info['message']
                    )
                    
                    if success:
                        # Обновляем в памяти и базе данных
                        self.bot.scheduler.scheduled_jobs[job_id]['is_paused'] = False
                        self.bot.db.update_schedule_pause_status(job_id, False)
                        
                        self.bot.send_message(chat_id, f"▶️ Расписание `{job_id}` возобновлено!")
                    else:
                        self.bot.send_message(chat_id, f"❌ Ошибка при возобновлении расписания `{job_id}`")
                
                else:
                    # Приостанавливаем работу - удаляем из планировщика но оставляем в памяти и базе данных
                    success = self.bot.scheduler.pause_job(job_id)
                    
                    if success:
                        # Обновляем в памяти и базе данных
                        self.bot.scheduler.scheduled_jobs[job_id]['is_paused'] = True
                        self.bot.db.update_schedule_pause_status(job_id, True)
                        
                        self.bot.send_message(chat_id, f"⏸️ Расписание `{job_id}` приостановлено!")
                    else:
                        self.bot.send_message(chat_id, f"❌ Ошибка при приостановке расписания `{job_id}`")
            else:
                self.bot.send_message(chat_id, "❌ Расписание не найдено или у вас нет прав.")
        except Exception as e:
            error_msg = f"❌ Ошибка при изменении статуса расписания: {e}"
            self.bot.send_message(chat_id, error_msg)
            logger.error(f"Error toggling job pause: {e}")