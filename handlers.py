"""Обработчики сообщений и команд"""

import logging
import time
from datetime import datetime
from schedule_manager import ScheduleManager

logger = logging.getLogger(__name__)

# Глобальные состояния пользователей
user_states = {}

class MessageHandlers:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.translator = bot_instance.translator
        # AI-based schedule parser (fallback)
        self.schedule_manager = ScheduleManager()

    def _get_lang(self, user_id):
        """Get user's language preference or default to Russian."""
        try:
            return self.bot.db.get_user_language(user_id)
        except Exception:
            return 'ru'
    
    def handle_start(self, chat_id, user_id):
        """Обработка команды /start"""
        lang = self._get_lang(user_id)
        title = self.translator.get_message('msg_start_title', lang)
        desc = self.translator.get_message('msg_start_description', lang)
        text = f"{title}\n\n{desc}"
        markup = {
            'inline_keyboard': [
                [
                    {'text': self.translator.get_button('btn_lang_en', lang), 'callback_data': 'lang:en'},
                    {'text': self.translator.get_button('btn_lang_ru', lang), 'callback_data': 'lang:ru'}
                ],
                [
                    {'text': self.translator.get_button('btn_schedule', lang), 'callback_data': 'cmd:schedule'}
                ],
                [
                    {'text': self.translator.get_button('btn_list', lang), 'callback_data': 'cmd:list'}
                ],
                [
                    {'text': self.translator.get_button('btn_manage', lang), 'callback_data': 'cmd:manage'},
                ],
                [
                    {'text': self.translator.get_button('btn_help', lang), 'callback_data': 'cmd:help'}
                ]
            ]
        }
        self.bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')
    
    def handle_help(self, chat_id, user_id):
        """Обработка команды /help"""
        lang = self._get_lang(user_id)
        title = self.translator.get_message('msg_help_title', lang)
        section = self.translator.get_message('msg_help_section_create', lang)
        step1 = self.translator.get_message('msg_help_step1', lang)
        step2 = self.translator.get_message('msg_help_step2', lang)
        step3 = self.translator.get_message('msg_help_step3', lang)
        step4 = self.translator.get_message('msg_help_step4', lang)
        step5 = self.translator.get_message('msg_help_step5', lang)
        examples = self.translator.get_message('msg_help_examples', lang)
        daily = self.translator.get_message('msg_help_daily', lang)
        every30 = self.translator.get_message('msg_help_every_minutes', lang)
        every2h = self.translator.get_message('msg_help_every_hours', lang)
        every10s = self.translator.get_message('msg_help_every_seconds', lang)
        cron_ex = self.translator.get_message('msg_help_cron_examples', lang)
        cron_mon = self.translator.get_message('msg_help_cron_monday', lang)
        cron_wd = self.translator.get_message('msg_help_cron_weekdays', lang)
        cron_m = self.translator.get_message('msg_help_cron_monthly', lang)
        cron_15 = self.translator.get_message('msg_help_cron_15th', lang)
        cron_15m = self.translator.get_message('msg_help_cron_15min', lang)
        cmd_sec = self.translator.get_message('msg_help_commands', lang)
        cmd_sch = self.translator.get_message('msg_help_cmd_schedule', lang)
        cmd_lst = self.translator.get_message('msg_help_cmd_list', lang)
        cmd_mng = self.translator.get_message('msg_help_cmd_manage', lang)
        cmd_hlp = self.translator.get_message('msg_help_cmd_help', lang)
        tip = self.translator.get_message('msg_help_tip', lang)
        
        text = (
            f"{title}\n\n"
            f"{section}\n"
            f"{step1}\n"
            f"{step2}\n"
            f"{step3}\n"
            f"{step4}\n"
            f"{step5}\n\n"
            f"{examples}\n"
            f"{daily}\n"
            f"{every30}\n"
            f"{every2h}\n"
            f"{every10s}\n\n"
            f"{cron_ex}\n"
            f"{cron_mon}\n"
            f"{cron_wd}\n"
            f"{cron_m}\n"
            f"{cron_15}\n"
            f"{cron_15m}\n\n"
            f"{cmd_sec}\n"
            f"{cmd_sch}\n"
            f"{cmd_lst}\n"
            f"{cmd_mng}\n"
            f"{cmd_hlp}\n\n"
            f"{tip}"
        )
        
        # Добавим быстрые кнопки команд внизу помощи
        markup = {'inline_keyboard': [[
            {'text': self.translator.get_button('btn_schedule', lang), 'callback_data': 'cmd:schedule'},
            {'text': self.translator.get_button('btn_list', lang), 'callback_data': 'cmd:list'},
            {'text': self.translator.get_button('btn_manage', lang), 'callback_data': 'cmd:manage'}
        ]]}
        self.bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')
    
    def handle_schedule(self, chat_id, user_id):
        """Обработка команды /schedule"""
        lang = self._get_lang(user_id)
        user_states[user_id] = {'step': 'chat_id'}
        title = self.translator.get_message('msg_schedule_title', lang)
        step1 = self.translator.get_message('msg_schedule_step1', lang)
        hint = self.translator.get_message('msg_schedule_step1_hint', lang)
        text = f"{title}\n\n{step1}\n{hint}"
        
        # Build markup with buttons
        keyboard = [[
            {'text': self.translator.get_button('btn_me', lang), 'callback_data': 'schedule:me'}
        ]]
        
        # Add saved contacts button if user has recent contacts
        recent_contacts = self.bot.db.get_recent_chat_ids(user_id)
        if recent_contacts:
            keyboard.append([
                {'text': self.translator.get_button('btn_saved_contacts', lang), 'callback_data': 'schedule:saved_contacts'}
            ])
        
        markup = {'inline_keyboard': keyboard}
        self.bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')
    
    def handle_list(self, chat_id, user_id):
        """Обработка команды /list"""
        lang = self._get_lang(user_id)
        user_jobs = {k: v for k, v in self.bot.scheduler.scheduled_jobs.items() 
                     if v['user_id'] == user_id}
        
        if not user_jobs:
            msg = self.translator.get_message('msg_no_active_schedules', lang)
            self.bot.send_message(chat_id, msg)
            return
        
        title = self.translator.get_message('msg_list_title', lang)
        active = self.translator.get_message('msg_list_status_active', lang)
        paused = self.translator.get_message('msg_list_status_paused', lang)
        id_lbl = self.translator.get_message('msg_list_id', lang)
        status_lbl = self.translator.get_message('msg_list_status', lang)
        target_lbl = self.translator.get_message('msg_list_target', lang)
        msg_lbl = self.translator.get_message('msg_list_message', lang)
        sch_lbl = self.translator.get_message('msg_list_schedule', lang)
        manage_msg = self.translator.get_message('msg_list_use_manage', lang)
        
        text = f"{title}\n\n"
        for job_id, job_info in user_jobs.items():
            status = paused if job_info['is_paused'] else active
            text += f"{id_lbl}{job_id}`\n"
            text += f"{status_lbl}{status}\n"
            text += f"{target_lbl}{job_info['chat_id']}\n"
            text += f"{msg_lbl}{job_info['message'][:50]}...\n"
            text += f"{sch_lbl}{job_info['schedule']}`\n"
            text += "─────────────\n"
        
        text += f"\n{manage_msg}"
        # Добавим кнопку управления после списка
        markup = {'inline_keyboard': [[{'text': self.translator.get_button('btn_manage', lang), 'callback_data': 'cmd:manage'}]]}
        self.bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')
    
    def handle_manage(self, chat_id, user_id):
        """Обработка команды /manage - показать интерактивный список"""
        lang = self._get_lang(user_id)
        user_jobs = {k: v for k, v in self.bot.scheduler.scheduled_jobs.items() if v['user_id'] == user_id}

        if not user_jobs:
            msg = self.translator.get_message('msg_no_schedules_manage', lang)
            self.bot.send_message(chat_id, msg)
            return

        # Для каждого расписания отправляем отдельное сообщение с inline-кнопками
        for job_id, job_info in user_jobs.items():
            text = self._build_job_text(job_id, job_info, lang)
            markup = self._build_job_markup(job_id, job_info, lang)
            # send a separate message per job with inline buttons
            self.bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')
    
    # --- Helpers for interactive manage ---
    def _build_job_text(self, job_id, job_info, lang='ru'):
        paused = self.translator.get_message('msg_list_status_paused', lang)
        active = self.translator.get_message('msg_list_status_active', lang)
        status = paused if job_info.get('is_paused') else active
        id_lbl = self.translator.get_message('msg_job_id', lang)
        status_lbl = self.translator.get_message('msg_job_status', lang)
        target_lbl = self.translator.get_message('msg_job_target', lang)
        msg_lbl = self.translator.get_message('msg_job_message', lang)
        sch_lbl = self.translator.get_message('msg_job_schedule', lang)
        text = (
            f"{id_lbl}{job_id}`\n"
            f"{status_lbl}{status}\n"
            f"{target_lbl}{job_info.get('chat_id')}\n"
            f"{msg_lbl}{job_info.get('message')}\n"
            f"{sch_lbl}{job_info.get('schedule')}`\n"
        )
        return text

    def _build_job_markup(self, job_id, job_info, lang='ru'):
        # Return inline keyboard depending on paused status
        if job_info.get('is_paused'):
            buttons = [
                {'text': self.translator.get_button('btn_resume', lang), 'callback_data': f'manage:resume:{job_id}'},
                {'text': self.translator.get_button('btn_delete', lang), 'callback_data': f'manage:delete:{job_id}'}
            ]
        else:
            buttons = [
                {'text': self.translator.get_button('btn_pause', lang), 'callback_data': f'manage:pause:{job_id}'},
                {'text': self.translator.get_button('btn_delete', lang), 'callback_data': f'manage:delete:{job_id}'}
            ]

        # Inline keyboard uses rows; put two buttons on one row
        return {'inline_keyboard': [buttons]}

    def _check_job_permission(self, job_id, user_id, cq_id):
        lang = self._get_lang(user_id)
        job = self.bot.scheduler.scheduled_jobs.get(job_id)
        if not job:
            not_found = self.translator.get_message('msg_callback_not_found', lang)
            self.bot.answer_callback_query(cq_id, text=not_found, show_alert=True)
            return None
        if job.get('user_id') != user_id:
            no_perm = self.translator.get_message('msg_callback_permissions', lang)
            self.bot.answer_callback_query(cq_id, text=no_perm, show_alert=True)
            return None
        return job

    def handle_callback_query(self, cq, cq_id, from_user, chat_id, message_id, data):
        """Обработка callback_query от inline-кнопок управления.

        data examples:
        - 'lang:en' / 'lang:ru' - language change
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

            # Handle language change
            if action == 'lang' and len(parts) == 2:
                new_lang = parts[1]
                
                # Small delay to ensure proper processing
                time.sleep(0.1)
                
                # Update bot menu to the new language
                try:
                    self.bot.set_bot_commands(new_lang)
                except Exception as e:
                    logger.error(f"Error updating bot commands: {e}")
                
                # Then save user language preference
                try:
                    self.bot.db.set_user_language(from_user, new_lang)
                except Exception as e:
                    logger.error(f"Error setting user language: {e}")
                
                # Acknowledge and refresh start menu
                lang_changed = self.translator.get_message('msg_callback_lang_changed', new_lang)
                self.bot.answer_callback_query(cq_id, text=f"{lang_changed}{new_lang.upper()}")
                self.handle_start(chat_id, from_user)
                return

            # Quick schedule actions (e.g. send to 'me')
            if action == 'schedule' and len(parts) >= 2:
                sub = parts[1]
                lang = self._get_lang(from_user)
                
                # set the user's target chat to the current chat (me)
                if sub == 'me':
                    # initialize or update state to step 'message'
                    user_states[from_user] = {'step': 'message', 'chat_id': chat_id}
                    # acknowledge and prompt for message text
                    self.bot.answer_callback_query(cq_id)
                    step2 = self.translator.get_message('msg_schedule_step2', lang)
                    self.bot.send_message(chat_id, step2)
                    return
                
                # Show saved contacts selector
                elif sub == 'saved_contacts':
                    self.bot.answer_callback_query(cq_id)
                    recent_contacts = self.bot.db.get_recent_chat_ids(from_user)
                    if not recent_contacts:
                        no_contacts = self.translator.get_message('msg_no_saved_contacts', lang)
                        self.bot.send_message(chat_id, no_contacts)
                        self.handle_schedule(chat_id, from_user)
                        return
                    
                    msg = self.translator.get_message('msg_select_saved_contact', lang)
                    keyboard = []
                    for contact_id in recent_contacts:
                        keyboard.append([
                            {'text': str(contact_id), 'callback_data': f'schedule:select_contact:{contact_id}'}
                        ])
                    markup = {'inline_keyboard': keyboard}
                    self.bot.send_message(chat_id, msg, reply_markup=markup)
                    return
                
                # Select a saved contact
                elif sub == 'select_contact' and len(parts) == 3:
                    try:
                        contact_id = int(parts[2])
                        user_states[from_user] = {'step': 'message', 'chat_id': contact_id}
                        self.bot.answer_callback_query(cq_id)
                        step2 = self.translator.get_message('msg_schedule_step2', lang)
                        self.bot.send_message(chat_id, step2)
                        return
                    except (ValueError, IndexError):
                        self.bot.answer_callback_query(cq_id)
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
                elif cmd == 'help':
                    self.handle_help(chat_id, from_user)
                else:
                    # unknown command
                    self.bot.answer_callback_query(cq_id)
                return

            if action == 'manage' and len(parts) == 3:
                lang = self._get_lang(from_user)
                subaction, job_id = parts[1], parts[2]

                job = self._check_job_permission(job_id, from_user, cq_id)
                if job is None:
                    return

                if subaction == 'pause':
                    success = self.bot.scheduler.pause_job(job_id)
                    if success:
                        job['is_paused'] = True
                        self.bot.db.update_schedule_pause_status(job_id, True)
                        new_text = self._build_job_text(job_id, job, lang)
                        new_markup = self._build_job_markup(job_id, job, lang)
                        self.bot.edit_message_text(chat_id, message_id, new_text, parse_mode='Markdown', reply_markup=new_markup)
                        paused_msg = self.translator.get_message('msg_callback_paused', lang)
                        self.bot.answer_callback_query(cq_id, text=paused_msg)
                    else:
                        error = self.translator.get_message('msg_callback_pause_error', lang)
                        self.bot.answer_callback_query(cq_id, text=error, show_alert=True)

                elif subaction == 'resume':
                    # Load schedule data from DB
                    schedules = self.bot.db.get_schedules(user_id=from_user)
                    target = None
                    for s in schedules:
                        if s['job_id'] == job_id:
                            target = s
                            break
                    if not target:
                        not_found = self.translator.get_message('msg_callback_not_found', lang)
                        self.bot.answer_callback_query(cq_id, text=not_found, show_alert=True)
                        return
                    success = self.bot.scheduler.resume_job(job_id, target['schedule_data'], target['chat_id'], target['message'])
                    if success:
                        job['is_paused'] = False
                        self.bot.db.update_schedule_pause_status(job_id, False)
                        new_text = self._build_job_text(job_id, job, lang)
                        new_markup = self._build_job_markup(job_id, job, lang)
                        self.bot.edit_message_text(chat_id, message_id, new_text, parse_mode='Markdown', reply_markup=new_markup)
                        resumed_msg = self.translator.get_message('msg_callback_resumed', lang)
                        self.bot.answer_callback_query(cq_id, text=resumed_msg)
                    else:
                        error = self.translator.get_message('msg_callback_resume_error', lang)
                        self.bot.answer_callback_query(cq_id, text=error, show_alert=True)

                elif subaction == 'delete':
                    # Edit the same message to ask for confirmation
                    confirm_prefix = self.translator.get_message('msg_confirm_delete', lang)
                    confirm_text = f"{confirm_prefix}{job_id}`\n\n" + self._build_job_text(job_id, job, lang)
                    confirm_markup = {'inline_keyboard': [[
                        {'text': self.translator.get_button('btn_confirm_delete', lang), 'callback_data': f'confirm_delete:{job_id}'},
                        {'text': self.translator.get_button('btn_cancel', lang), 'callback_data': f'cancel_delete:{job_id}'}
                    ]]}
                    self.bot.edit_message_text(chat_id, message_id, confirm_text, parse_mode='Markdown', reply_markup=confirm_markup)
                    self.bot.answer_callback_query(cq_id)
                else:
                    self.bot.answer_callback_query(cq_id)

            elif action == 'confirm_delete' and len(parts) == 2:
                lang = self._get_lang(from_user)
                job_id = parts[1]
                job = self._check_job_permission(job_id, from_user, cq_id)
                if job is None:
                    return

                # Proceed to delete
                self.bot.scheduler.delete_job(job_id)
                self.bot.db.delete_schedule(job_id)
                # remove from memory
                del self.bot.scheduler.scheduled_jobs[job_id]
                
                # Answer callback query first to acknowledge button press
                deleted_msg = self.translator.get_message('msg_callback_deleted', lang)
                self.bot.answer_callback_query(cq_id, text=deleted_msg)
                
                # Edit the inline message to show deletion status
                deleted_status = self.translator.get_message('msg_list_status_deleted', lang)
                id_lbl = self.translator.get_message('msg_job_id', lang)
                status_lbl = self.translator.get_message('msg_job_status', lang)
                deleted_text = (
                    f"{id_lbl}{job_id}`\n"
                    f"{status_lbl}{deleted_status}\n"
                )
                # Send message with no buttons
                self.bot.edit_message_text(chat_id, message_id, deleted_text, parse_mode='Markdown', reply_markup={})

            elif action == 'cancel_delete' and len(parts) == 2:
                lang = self._get_lang(from_user)
                job_id = parts[1]
                job = self._check_job_permission(job_id, from_user, cq_id)
                if job is None:
                    return
                # restore original message and buttons
                orig_text = self._build_job_text(job_id, job, lang)
                orig_markup = self._build_job_markup(job_id, job, lang)
                self.bot.edit_message_text(chat_id, message_id, orig_text, parse_mode='Markdown', reply_markup=orig_markup)
                cancelled_msg = self.translator.get_message('msg_callback_cancelled', lang)
                self.bot.answer_callback_query(cq_id, text=cancelled_msg)

            else:
                # Unknown action
                self.bot.answer_callback_query(cq_id)

        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
            try:
                lang = self._get_lang(from_user)
                error_msg = self.translator.get_message('msg_error_internal', lang)
                self.bot.answer_callback_query(cq_id, text=error_msg, show_alert=True)
            except Exception:
                pass
    
    def handle_text_message(self, chat_id, user_id, text):
        """Обработка текстовых сообщений для мастера планирования и управления"""
        if user_id not in user_states:
            return
        
        lang = self._get_lang(user_id)
        state = user_states[user_id]
        step = state['step']
        
        if step == 'chat_id':
            target_chat = text if text.lower() != 'me' else chat_id
            state['chat_id'] = target_chat
            # Save to recent contacts if it's a valid number
            try:
                if str(target_chat).lstrip('-').isdigit():
                    self.bot.db.add_recent_chat_id(user_id, int(target_chat))
            except Exception as e:
                logger.warning(f"Could not save recent chat_id: {e}")
            state['step'] = 'message'
            step2 = self.translator.get_message('msg_schedule_step2', lang)
            self.bot.send_message(chat_id, step2)
        
        
        elif step == 'message':
            state['message'] = text
            state['step'] = 'schedule'
            title = self.translator.get_message('msg_schedule_step3_title', lang)
            examples = self.translator.get_message('msg_schedule_examples', lang)
            daily = self.translator.get_message('msg_help_daily', lang)
            every30 = self.translator.get_message('msg_help_every_minutes', lang)
            every2h = self.translator.get_message('msg_help_every_hours', lang)
            cron_mon = self.translator.get_message('msg_help_cron_monday', lang)
            hint = self.translator.get_message('msg_schedule_step3_hint', lang)
            msg_text = f"{title}\n\n{examples}\n{daily}\n{every30}\n{every2h}\n{cron_mon}\n\n{hint}"
            self.bot.send_message(chat_id, msg_text)
        
        elif step == 'schedule':
            self.create_schedule(chat_id, user_id, text, state)
        
        elif step == 'manage_select':
            self.handle_manage_selection(chat_id, user_id, text)
        
        elif step == 'manage_action':
            self.handle_manage_action(chat_id, user_id, text)
    
    def create_schedule(self, chat_id, user_id, schedule_text, state):
        """Создание нового расписания"""
        lang = self._get_lang(user_id)
        job_id = f"job_{user_id}_{int(datetime.now().timestamp())}"
        
        try:
            schedule_text = schedule_text.strip()
            
            # All schedules are converted to cron via AI parser
            try:
                cron_expr = self.schedule_manager._parse_schedule_with_ai(schedule_text)
                schedule_data = self.bot.scheduler.create_cron_schedule(job_id, state['chat_id'], state['message'], cron_expr)
            except Exception as e:
                error_prefix = self.translator.get_message('msg_error_schedule_unknown', lang)
                raise ValueError(f"{error_prefix}{e}")
            
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
                schedule_data=schedule_data,
                is_paused=False
            )
            
            # Send success message with quick action buttons
            title = self.translator.get_message('msg_success_created', lang)
            id_lbl = self.translator.get_message('msg_success_id', lang)
            sch_lbl = self.translator.get_message('msg_success_schedule', lang)
            tgt_lbl = self.translator.get_message('msg_success_target', lang)
            success_text = (
                f"{title}\n\n"
                f"{id_lbl}{job_id}`\n"
                f"{sch_lbl}{schedule_data['description']}`\n"
                f"{tgt_lbl}{state['chat_id']}\n"
            )
            success_markup = {'inline_keyboard': [
                [
                    {'text': self.translator.get_button('btn_list', lang), 'callback_data': 'cmd:list'},
                    {'text': self.translator.get_button('btn_manage', lang), 'callback_data': 'cmd:manage'}
                ],
                [
                    {'text': self.translator.get_button('btn_delete', lang), 'callback_data': f'manage:delete:{job_id}'}
                ]
            ]}
            self.bot.send_message(chat_id, success_text, reply_markup=success_markup, parse_mode='Markdown')
            
            # Очищаем состояние пользователя (только если есть)
            if user_id in user_states:
                del user_states[user_id]
            
        except Exception as e:
            # Preserve the target chat and message so user can re-enter schedule
            logger.error(f"Error creating schedule: {e}")
            # Ensure state exists and points back to schedule step
            user_states[user_id] = {
                'step': 'schedule',
                'chat_id': state.get('chat_id') if isinstance(state, dict) else None,
                'message': state.get('message') if isinstance(state, dict) else None
            }

            # Prompt user to re-enter schedule (keep chat_id and message remembered)
            error_msg = self.translator.get_message('msg_error_create', lang)
            retry_msg = self.translator.get_message('msg_error_retry', lang)
            restart_msg = self.translator.get_message('msg_error_restart', lang)
            error_text = (
                f"{error_msg}{e}\n\n"
                f"{retry_msg}\n"
                f"{restart_msg}"
            )
            retry_markup = {'inline_keyboard': [[
                {'text': self.translator.get_button('btn_schedule', lang), 'callback_data': 'cmd:schedule'}
            ]]}

            # Try to send the richer message; if that fails, fall back to a simple send
            try:
                self.bot.send_message(chat_id, error_text, reply_markup=retry_markup, parse_mode='Markdown')
            except Exception as send_err:
                logger.error(f"Failed to send error message with markup: {send_err}")
                try:
                    self.bot.send_message(chat_id, error_text)
                except Exception as send_err2:
                    logger.error(f"Failed to send fallback error message: {send_err2}")
    