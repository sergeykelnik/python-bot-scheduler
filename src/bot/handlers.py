"""
Telegram Bot Message and Callback Handlers.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional

from src.services.translation_service import TranslationService
from src.services.scheduler_service import SchedulerService
from src.services.ai_service import AIService
from src.core.database import Database

logger = logging.getLogger(__name__)

# Global user state storage (in-memory)
# Format: user_id -> {'step': str, 'chat_id': str, 'message': str, ...}
user_states: Dict[int, Dict[str, Any]] = {}

class MessageHandlers:
    """Class handling Telegram messages and callbacks."""
    
    def __init__(self, bot_instance):
        """
        Initialize handlers.
        
        Args:
            bot_instance: Instance of TelegramBot.
        """
        self.bot = bot_instance
        # Type hinting for better IDE support
        self.translator: TranslationService = bot_instance.translator
        self.db: Database = bot_instance.db
        self.scheduler: SchedulerService = bot_instance.scheduler
        self.ai_service: AIService = bot_instance.ai_service

    def _get_lang(self, user_id: int) -> str:
        """Get user's language preference."""
        try:
            return self.db.get_user_language(user_id)
        except Exception:
            return 'ru'
    
    # --- Command Handlers ---

    def handle_start(self, chat_id: str, user_id: int):
        """Handle /start command."""
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

    def handle_help(self, chat_id: str, user_id: int):
        """Handle /help command."""
        lang = self._get_lang(user_id)
        # Fetching all help strings
        msg_keys = [
            'msg_help_title', 'msg_help_section_create', 'msg_help_step1', 
            'msg_help_step2', 'msg_help_step3', 'msg_help_step4', 'msg_help_step5',
            'msg_help_examples', 'msg_help_daily', 'msg_help_every_minutes',
            'msg_help_every_hours', 'msg_help_every_seconds', 'msg_help_cron_examples',
            'msg_help_cron_monday', 'msg_help_cron_weekdays', 'msg_help_cron_monthly',
            'msg_help_cron_15th', 'msg_help_cron_15min', 'msg_help_commands',
            'msg_help_cmd_schedule', 'msg_help_cmd_list', 'msg_help_cmd_manage',
            'msg_help_cmd_help', 'msg_help_tip'
        ]
        msgs = {key: self.translator.get_message(key, lang) for key in msg_keys}
        
        text = (
            f"{msgs['msg_help_title']}\n\n"
            f"{msgs['msg_help_section_create']}\n"
            f"{msgs['msg_help_step1']}\n"
            f"{msgs['msg_help_step2']}\n"
            f"{msgs['msg_help_step3']}\n"
            f"{msgs['msg_help_step4']}\n"
            f"{msgs['msg_help_step5']}\n\n"
            f"{msgs['msg_help_examples']}\n"
            f"{msgs['msg_help_daily']}\n"
            f"{msgs['msg_help_every_minutes']}\n"
            f"{msgs['msg_help_every_hours']}\n"
            f"{msgs['msg_help_every_seconds']}\n\n"
            f"{msgs['msg_help_cron_examples']}\n"
            f"{msgs['msg_help_cron_monday']}\n"
            f"{msgs['msg_help_cron_weekdays']}\n"
            f"{msgs['msg_help_cron_monthly']}\n"
            f"{msgs['msg_help_cron_15th']}\n"
            f"{msgs['msg_help_cron_15min']}\n\n"
            f"{msgs['msg_help_commands']}\n"
            f"{msgs['msg_help_cmd_schedule']}\n"
            f"{msgs['msg_help_cmd_list']}\n"
            f"{msgs['msg_help_cmd_manage']}\n"
            f"{msgs['msg_help_cmd_help']}\n\n"
            f"{msgs['msg_help_tip']}"
        )
        
        markup = {'inline_keyboard': [[
            {'text': self.translator.get_button('btn_schedule', lang), 'callback_data': 'cmd:schedule'},
            {'text': self.translator.get_button('btn_list', lang), 'callback_data': 'cmd:list'},
            {'text': self.translator.get_button('btn_manage', lang), 'callback_data': 'cmd:manage'}
        ]]}
        self.bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')

    def handle_schedule(self, chat_id: str, user_id: int):
        """Handle /schedule command."""
        lang = self._get_lang(user_id)
        user_states[user_id] = {'step': 'chat_id'}
        
        title = self.translator.get_message('msg_schedule_title', lang)
        step1 = self.translator.get_message('msg_schedule_step1', lang)
        hint = self.translator.get_message('msg_schedule_step1_hint', lang)
        text = f"{title}\n\n{step1}\n{hint}"
        
        keyboard = [[
            {'text': self.translator.get_button('btn_me', lang), 'callback_data': 'schedule:me'}
        ]]
        
        recent_contacts = self.db.get_recent_chat_ids(user_id)
        if recent_contacts:
            keyboard.append([
                {'text': self.translator.get_button('btn_saved_contacts', lang), 'callback_data': 'schedule:saved_contacts'}
            ])
        
        markup = {'inline_keyboard': keyboard}
        self.bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')

    def handle_list(self, chat_id: str, user_id: int):
        """Handle /list command."""
        lang = self._get_lang(user_id)
        # Fetch schedules from DB
        all_schedules = self.db.get_schedules(user_id)
        
        if not all_schedules:
            msg = self.translator.get_message('msg_no_active_schedules', lang)
            self.bot.send_message(chat_id, msg)
            return
        
        msgs = {k: self.translator.get_message(k, lang) for k in [
            'msg_list_title', 'msg_list_status_active', 'msg_list_status_paused',
            'msg_list_id', 'msg_list_status', 'msg_list_target', 'msg_list_message',
            'msg_list_schedule', 'msg_list_use_manage'
        ]}
        
        text = f"{msgs['msg_list_title']}\n\n"
        for job in all_schedules:
            status = msgs['msg_list_status_paused'] if job['is_paused'] else msgs['msg_list_status_active']
            schedule_desc = job['schedule_data'].get('description', 'Unknown')
            
            text += f"{msgs['msg_list_id']}{job['job_id']}`\n"
            text += f"{msgs['msg_list_status']}{status}\n"
            text += f"{msgs['msg_list_target']}{job['chat_id']}\n"
            text += f"{msgs['msg_list_message']}{job['message'][:50]}...\n"
            text += f"{msgs['msg_list_schedule']}{schedule_desc}`\n"
            text += "─────────────\n"
        
        text += f"\n{msgs['msg_list_use_manage']}"
        markup = {'inline_keyboard': [[{'text': self.translator.get_button('btn_manage', lang), 'callback_data': 'cmd:manage'}]]}
        self.bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')

    def handle_manage(self, chat_id: str, user_id: int):
        """Handle /manage command."""
        lang = self._get_lang(user_id)
        all_schedules = self.db.get_schedules(user_id)

        if not all_schedules:
            msg = self.translator.get_message('msg_no_schedules_manage', lang)
            self.bot.send_message(chat_id, msg)
            return

        for job in all_schedules:
            # Transform DB row dict to the format expected by helper methods
            # (Essentially same structure, just ensuring compatibility)
            job_info = {
                'job_id': job['job_id'],
                'chat_id': job['chat_id'],
                'message': job['message'],
                'schedule': job['schedule_data'].get('description'),
                'is_paused': job['is_paused'],
                'user_id': job['user_id']
            }
            
            text = self._build_job_text(job['job_id'], job_info, lang)
            markup = self._build_job_markup(job['job_id'], job_info, lang)
            self.bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')

    # --- Interaction Helpers ---

    def _build_job_text(self, job_id, job_info, lang='ru'):
        msgs = {k: self.translator.get_message(k, lang) for k in [
            'msg_list_status_paused', 'msg_list_status_active', 'msg_job_id',
            'msg_job_status', 'msg_job_target', 'msg_job_message', 'msg_job_schedule'
        ]}
        
        status = msgs['msg_list_status_paused'] if job_info.get('is_paused') else msgs['msg_list_status_active']
        
        text = (
            f"{msgs['msg_job_id']}{job_id}`\n"
            f"{msgs['msg_job_status']}{status}\n"
            f"{msgs['msg_job_target']}{job_info.get('chat_id')}\n"
            f"{msgs['msg_job_message']}{job_info.get('message')}\n"
            f"{msgs['msg_job_schedule']}{job_info.get('schedule')}`\n"
        )
        return text

    def _build_job_markup(self, job_id, job_info, lang='ru'):
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
        return {'inline_keyboard': [buttons]}

    def _get_job_from_db(self, job_id: str, user_id: int):
        """Helper to get job and check permissions."""
        jobs = self.db.get_schedules(user_id)
        for job in jobs:
            if job['job_id'] == job_id:
                return job
        return None

    # --- Callback Query Handler ---

    def handle_callback_query(self, cq, cq_id, from_user, chat_id, message_id, data):
        """Handle inline button callbacks."""
        try:
            if not data:
                self.bot.answer_callback_query(cq_id)
                return

            parts = data.split(':')
            action = parts[0]
            lang = self._get_lang(from_user)

            # Language Change
            if action == 'lang' and len(parts) == 2:
                new_lang = parts[1]
                time.sleep(0.1)
                self.bot.set_bot_commands(new_lang) # Reset menu commands
                self.db.set_user_language(from_user, new_lang)
                
                lang_changed = self.translator.get_message('msg_callback_lang_changed', new_lang)
                self.bot.answer_callback_query(cq_id, text=f"{lang_changed}{new_lang.upper()}")
                self.handle_start(chat_id, from_user) # Refresh start message
                return

            # Schedule Creation Flow (Buttons)
            if action == 'schedule' and len(parts) >= 2:
                sub = parts[1]
                
                if sub == 'me':
                    user_states[from_user] = {'step': 'message', 'chat_id': chat_id}
                    self.bot.answer_callback_query(cq_id)
                    step2 = self.translator.get_message('msg_schedule_step2', lang)
                    self.bot.send_message(chat_id, step2)
                    return
                
                elif sub == 'saved_contacts':
                    self.bot.answer_callback_query(cq_id)
                    recent_contacts = self.db.get_recent_chat_ids(from_user)
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
                
                elif sub == 'select_contact' and len(parts) == 3:
                    try:
                        contact_id = int(parts[2])
                        user_states[from_user] = {'step': 'message', 'chat_id': contact_id}
                        self.bot.answer_callback_query(cq_id)
                        step2 = self.translator.get_message('msg_schedule_step2', lang)
                        self.bot.send_message(chat_id, step2)
                        return
                    except ValueError:
                        self.bot.answer_callback_query(cq_id)
                        return

            # Main Menu Navigation
            if action == 'cmd' and len(parts) >= 2:
                cmd = parts[1]
                self.bot.answer_callback_query(cq_id)
                if cmd == 'schedule':
                    self.handle_schedule(chat_id, from_user)
                elif cmd == 'list':
                    self.handle_list(chat_id, from_user)
                elif cmd == 'manage':
                    self.handle_manage(chat_id, from_user)
                elif cmd == 'help':
                    self.handle_help(chat_id, from_user)
                return

            # Management Actions (Pause/Resume/Delete)
            if action == 'manage' and len(parts) == 3:
                subaction, job_id = parts[1], parts[2]
                
                # Check permissions and existing job
                job_db = self._get_job_from_db(job_id, from_user)
                if not job_db:
                    not_found = self.translator.get_message('msg_callback_not_found', lang)
                    self.bot.answer_callback_query(cq_id, text=not_found, show_alert=True)
                    return

                # Construct simple object for helper functions
                job_obj = {
                    'job_id': job_db['job_id'],
                    'chat_id': job_db['chat_id'],
                    'message': job_db['message'],
                    'schedule': job_db['schedule_data'].get('description'),
                    'is_paused': job_db['is_paused'],
                    'user_id': job_db['user_id']
                }

                if subaction == 'pause':
                    if self.scheduler.pause_job(job_id):
                        self.db.update_schedule_pause_status(job_id, True)
                        job_obj['is_paused'] = True
                        
                        new_text = self._build_job_text(job_id, job_obj, lang)
                        new_markup = self._build_job_markup(job_id, job_obj, lang)
                        self.bot.edit_message_text(chat_id, message_id, new_text, parse_mode='Markdown', reply_markup=new_markup)
                        
                        msg = self.translator.get_message('msg_callback_paused', lang)
                        self.bot.answer_callback_query(cq_id, text=msg)
                    else:
                        err = self.translator.get_message('msg_callback_pause_error', lang)
                        self.bot.answer_callback_query(cq_id, text=err, show_alert=True)

                elif subaction == 'resume':
                    schedule_data = job_db['schedule_data']
                    if self.scheduler.resume_job(job_id, schedule_data['expression'], job_db['chat_id'], job_db['message']):
                        self.db.update_schedule_pause_status(job_id, False)
                        job_obj['is_paused'] = False
                        
                        new_text = self._build_job_text(job_id, job_obj, lang)
                        new_markup = self._build_job_markup(job_id, job_obj, lang)
                        self.bot.edit_message_text(chat_id, message_id, new_text, parse_mode='Markdown', reply_markup=new_markup)
                        
                        msg = self.translator.get_message('msg_callback_resumed', lang)
                        self.bot.answer_callback_query(cq_id, text=msg)
                    else:
                        err = self.translator.get_message('msg_callback_resume_error', lang)
                        self.bot.answer_callback_query(cq_id, text=err, show_alert=True)

                elif subaction == 'delete':
                    confirm_prefix = self.translator.get_message('msg_confirm_delete', lang)
                    confirm_text = f"{confirm_prefix}{job_id}`\n\n" + self._build_job_text(job_id, job_obj, lang)
                    confirm_markup = {'inline_keyboard': [[
                        {'text': self.translator.get_button('btn_confirm_delete', lang), 'callback_data': f'confirm_delete:{job_id}'},
                        {'text': self.translator.get_button('btn_cancel', lang), 'callback_data': f'cancel_delete:{job_id}'}
                    ]]}
                    self.bot.edit_message_text(chat_id, message_id, confirm_text, parse_mode='Markdown', reply_markup=confirm_markup)
                    self.bot.answer_callback_query(cq_id)

            elif action == 'confirm_delete' and len(parts) == 2:
                job_id = parts[1]
                # Optimistically try delete
                self.scheduler.delete_job(job_id)
                self.db.delete_schedule(job_id)
                
                deleted_msg = self.translator.get_message('msg_callback_deleted', lang)
                self.bot.answer_callback_query(cq_id, text=deleted_msg)
                
                deleted_status = self.translator.get_message('msg_list_status_deleted', lang)
                lbl_id = self.translator.get_message('msg_job_id', lang)
                lbl_st = self.translator.get_message('msg_job_status', lang)
                
                text = f"{lbl_id}{job_id}`\n{lbl_st}{deleted_status}\n"
                self.bot.edit_message_text(chat_id, message_id, text, parse_mode='Markdown', reply_markup={})

            elif action == 'cancel_delete' and len(parts) == 2:
                job_id = parts[1]
                job_db = self._get_job_from_db(job_id, from_user)
                if not job_db:
                    return
                # Reconstruct object
                job_obj = {
                    'job_id': job_db['job_id'],
                    'chat_id': job_db['chat_id'],
                    'message': job_db['message'],
                    'schedule': job_db['schedule_data'].get('description'),
                    'is_paused': job_db['is_paused'],
                    'user_id': job_db['user_id']
                }
                
                orig_text = self._build_job_text(job_id, job_obj, lang)
                orig_markup = self._build_job_markup(job_id, job_obj, lang)
                self.bot.edit_message_text(chat_id, message_id, orig_text, parse_mode='Markdown', reply_markup=orig_markup)
                
                msg = self.translator.get_message('msg_callback_cancelled', lang)
                self.bot.answer_callback_query(cq_id, text=msg)

        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
            try:
                err = self.translator.get_message('msg_error_internal', self._get_lang(from_user))
                self.bot.answer_callback_query(cq_id, text=err, show_alert=True)
            except:
                pass

    # --- Text Message Handler (Wizard) ---

    def handle_text_message(self, chat_id: str, user_id: int, text: str):
        """Handle text input for schedule wizard."""
        if user_id not in user_states:
            return
        
        lang = self._get_lang(user_id)
        state = user_states[user_id]
        step = state['step']
        
        if step == 'chat_id':
            target_chat = text if text.lower() != 'me' else chat_id
            state['chat_id'] = target_chat
            
            # Try add to recent contacts
            try:
                if str(target_chat).lstrip('-').isdigit():
                    self.db.add_recent_chat_id(user_id, int(target_chat))
            except Exception as e:
                logger.warning(f"Could not save recent chat_id: {e}")
            
            state['step'] = 'message'
            step2 = self.translator.get_message('msg_schedule_step2', lang)
            self.bot.send_message(chat_id, step2)
        
        elif step == 'message':
            state['message'] = text
            state['step'] = 'schedule'
            
            msgs = {k: self.translator.get_message(k, lang) for k in [
                'msg_schedule_step3_title', 'msg_schedule_examples', 'msg_help_daily', 
                'msg_help_every_minutes', 'msg_help_every_hours', 'msg_help_cron_monday', 
                'msg_schedule_step3_hint'
            ]}
            msg_text = (
                f"{msgs['msg_schedule_step3_title']}\n\n"
                f"{msgs['msg_schedule_examples']}\n"
                f"{msgs['msg_help_daily']}\n"
                f"{msgs['msg_help_every_minutes']}\n"
                f"{msgs['msg_help_every_hours']}\n"
                f"{msgs['msg_help_cron_monday']}\n\n"
                f"{msgs['msg_schedule_step3_hint']}"
            )
            self.bot.send_message(chat_id, msg_text)
        
        elif step == 'schedule':
            self._create_schedule_from_wizard(chat_id, user_id, text, state)

    def _create_schedule_from_wizard(self, chat_id: str, user_id: int, schedule_text: str, state: dict):
        """Finalize schedule creation from wizard state."""
        lang = self._get_lang(user_id)
        job_id = f"job_{user_id}_{int(datetime.now().timestamp())}"
        
        try:
            schedule_text = schedule_text.strip()
            
            # AI Parse
            try:
                cron_expr = self.ai_service.parse_schedule_to_cron(schedule_text)
                # Add to scheduler
                schedule_data = self.scheduler.add_job(job_id, state['chat_id'], state['message'], cron_expr)
            except ValueError as e:
                err_prefix = self.translator.get_message('msg_error_schedule_unknown', lang)
                raise ValueError(f"{err_prefix}{e}")
            
            # Save to DB
            self.db.save_schedule(
                job_id=job_id,
                user_id=user_id,
                chat_id=state['chat_id'],
                message=state['message'],
                schedule_data=schedule_data,
                is_paused=False
            )
            
            # Success
            msgs = {k: self.translator.get_message(k, lang) for k in [
                'msg_success_created', 'msg_success_id', 'msg_success_schedule', 'msg_success_target'
            ]}
            
            success_text = (
                f"{msgs['msg_success_created']}\n\n"
                f"{msgs['msg_success_id']}{job_id}`\n"
                f"{msgs['msg_success_schedule']}{schedule_data['description']}`\n"
                f"{msgs['msg_success_target']}{state['chat_id']}\n"
            )
            
            markup = {'inline_keyboard': [
                [
                    {'text': self.translator.get_button('btn_list', lang), 'callback_data': 'cmd:list'},
                    {'text': self.translator.get_button('btn_manage', lang), 'callback_data': 'cmd:manage'}
                ],
                [
                    {'text': self.translator.get_button('btn_delete', lang), 'callback_data': f'manage:delete:{job_id}'}
                ]
            ]}
            self.bot.send_message(chat_id, success_text, reply_markup=markup, parse_mode='Markdown')
            
            # Clear state
            if user_id in user_states:
                del user_states[user_id]
                
        except Exception as e:
            logger.error(f"Error creating schedule: {e}")
            # Recoverable error state - keep user in 'schedule' step
            user_states[user_id] = {
                'step': 'schedule',
                'chat_id': state.get('chat_id'),
                'message': state.get('message')
            }
            
            msgs = {k: self.translator.get_message(k, lang) for k in [
                'msg_error_create', 'msg_error_retry', 'msg_error_restart'
            ]}
            
            error_text = (
                f"{msgs['msg_error_create']}{e}\n\n"
                f"{msgs['msg_error_retry']}\n"
                f"{msgs['msg_error_restart']}"
            )
            retry_markup = {'inline_keyboard': [[
                {'text': self.translator.get_button('btn_schedule', lang), 'callback_data': 'cmd:schedule'}
            ]]}
            
            self.bot.send_message(chat_id, error_text, reply_markup=retry_markup, parse_mode='Markdown')
