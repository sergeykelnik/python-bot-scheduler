"""
Shared helpers used by both handlers and callbacks routers.
"""

import logging
from typing import List, Dict

from aiogram import Bot

from src.bot.database import Database
from src.bot.translation_service import TranslationService

logger = logging.getLogger(__name__)


async def get_lang(db: Database, user_id: int) -> str:
    """Get user language preference with fallback."""
    try:
        return await db.get_user_language(user_id)
    except Exception:
        return "ru"


async def validate_chat_id(bot: Bot, chat_id: str) -> bool:
    """Check whether the bot can reach the given chat_id.

    Returns True if reachable, False otherwise.
    """
    try:
        await bot.get_chat(chat_id)
        return True
    except Exception as e:
        logger.debug("Chat %s is unreachable: %s", chat_id, e)
        return False


def build_help_text(tr: TranslationService, lang: str) -> str:
    """Build the full /help message text."""
    keys = [
        "msg_help_title", "msg_help_section_create", "msg_help_step1",
        "msg_help_step2", "msg_help_step3", "msg_help_step4", "msg_help_step5",
        "msg_help_examples", "msg_help_daily", "msg_help_every_minutes",
        "msg_help_every_hours", "msg_help_every_seconds", "msg_help_cron_examples",
        "msg_help_cron_monday", "msg_help_cron_weekdays", "msg_help_cron_monthly",
        "msg_help_cron_15th", "msg_help_cron_15min", "msg_help_commands",
        "msg_help_cmd_schedule", "msg_help_cmd_list", "msg_help_cmd_manage",
        "msg_help_cmd_help", "msg_help_tip",
    ]
    m = {k: tr.get_message(k, lang) for k in keys}
    return (
        f"{m['msg_help_title']}\n\n"
        f"{m['msg_help_section_create']}\n"
        f"{m['msg_help_step1']}\n{m['msg_help_step2']}\n{m['msg_help_step3']}\n"
        f"{m['msg_help_step4']}\n{m['msg_help_step5']}\n\n"
        f"{m['msg_help_examples']}\n"
        f"{m['msg_help_daily']}\n{m['msg_help_every_minutes']}\n"
        f"{m['msg_help_every_hours']}\n{m['msg_help_every_seconds']}\n\n"
        f"{m['msg_help_cron_examples']}\n"
        f"{m['msg_help_cron_monday']}\n{m['msg_help_cron_weekdays']}\n"
        f"{m['msg_help_cron_monthly']}\n{m['msg_help_cron_15th']}\n"
        f"{m['msg_help_cron_15min']}\n\n"
        f"{m['msg_help_commands']}\n"
        f"{m['msg_help_cmd_schedule']}\n{m['msg_help_cmd_list']}\n"
        f"{m['msg_help_cmd_manage']}\n{m['msg_help_cmd_help']}\n\n"
        f"{m['msg_help_tip']}"
    )


def build_list_text(schedules: List[Dict], tr: TranslationService, lang: str) -> str:
    """Build the /list message text from a list of schedule dicts."""
    keys = [
        "msg_list_title", "msg_list_status_active", "msg_list_status_paused",
        "msg_list_id", "msg_list_status", "msg_list_target",
        "msg_list_message", "msg_list_schedule", "msg_list_use_manage",
    ]
    m = {k: tr.get_message(k, lang) for k in keys}

    text = f"{m['msg_list_title']}\n\n"
    for job in schedules:
        status = m["msg_list_status_paused"] if job["is_paused"] else m["msg_list_status_active"]
        desc = job["schedule_data"].get("description", "Unknown")
        msg_preview = job["message"][:50] + ("…" if len(job["message"]) > 50 else "")
        text += (
            f"{m['msg_list_id']}{job['job_id']}`\n"
            f"{m['msg_list_status']}{status}\n"
            f"{m['msg_list_target']}{job['chat_id']}\n"
            f"{m['msg_list_message']}{msg_preview}\n"
            f"{m['msg_list_schedule']}{desc}`\n"
            "─────────────\n"
        )
    text += f"\n{m['msg_list_use_manage']}"
    return text


def build_job_text(job: dict, tr: TranslationService, lang: str) -> str:
    """Build a single job card text for /manage view."""
    keys = [
        "msg_list_status_paused", "msg_list_status_active",
        "msg_job_id", "msg_job_status", "msg_job_target",
        "msg_job_message", "msg_job_schedule",
    ]
    m = {k: tr.get_message(k, lang) for k in keys}
    status = m["msg_list_status_paused"] if job.get("is_paused") else m["msg_list_status_active"]
    sched_desc = job.get("schedule_data", {}).get("description") or job.get("schedule", "")
    return (
        f"{m['msg_job_id']}{job.get('job_id', '')}`\n"
        f"{m['msg_job_status']}{status}\n"
        f"{m['msg_job_target']}{job.get('chat_id', '')}\n"
        f"{m['msg_job_message']}{job.get('message', '')}\n"
        f"{m['msg_job_schedule']}{sched_desc}`\n"
    )

