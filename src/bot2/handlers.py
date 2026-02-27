"""
Command & text-message handlers (aiogram Router).
"""

import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.bot2.states import ScheduleWizard
from src.bot2.database import Database
from src.bot2.translation_service import TranslationService
from src.bot2.scheduler_service import SchedulerService
from src.bot2.ai_service import AIService
from src.bot2 import keyboards as kb

logger = logging.getLogger(__name__)

router = Router(name="handlers")


# ------------------------------------------------------------------
# Helpers – pulled from dispatcher workflow_data
# ------------------------------------------------------------------

def _services(data: dict):
    """Unpack services stored in dispatcher workflow_data / middleware."""
    return (
        data["db"],
        data["translator"],
        data["scheduler"],
        data["ai_service"],
    )


async def _lang(db: Database, user_id: int) -> str:
    try:
        return await db.get_user_language(user_id)
    except Exception:
        return "ru"


# ------------------------------------------------------------------
# /start
# ------------------------------------------------------------------

@router.message(Command("start"))
async def cmd_start(message: Message, db: Database, translator: TranslationService, **_):
    lang = await _lang(db, message.from_user.id)
    title = translator.get_message("msg_start_title", lang)
    desc = translator.get_message("msg_start_description", lang)
    await message.answer(f"{title}\n\n{desc}", reply_markup=kb.start_keyboard(translator, lang))


# ------------------------------------------------------------------
# /help
# ------------------------------------------------------------------

@router.message(Command("help"))
async def cmd_help(message: Message, db: Database, translator: TranslationService, **_):
    lang = await _lang(db, message.from_user.id)
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
    m = {k: translator.get_message(k, lang) for k in keys}

    text = (
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
    await message.answer(text, reply_markup=kb.help_keyboard(translator, lang))


# ------------------------------------------------------------------
# /schedule  – enter the wizard
# ------------------------------------------------------------------

@router.message(Command("schedule"))
async def cmd_schedule(message: Message, state: FSMContext, db: Database, translator: TranslationService, **_):
    lang = await _lang(db, message.from_user.id)
    await state.set_state(ScheduleWizard.waiting_chat_id)

    title = translator.get_message("msg_schedule_title", lang)
    step1 = translator.get_message("msg_schedule_step1", lang)
    hint = translator.get_message("msg_schedule_step1_hint", lang)

    recent = await db.get_recent_chat_ids(message.from_user.id)
    markup = kb.schedule_step1_keyboard(translator, lang, has_recent_contacts=bool(recent))

    await message.answer(f"{title}\n\n{step1}\n{hint}", reply_markup=markup)


# ------------------------------------------------------------------
# /list
# ------------------------------------------------------------------

@router.message(Command("list"))
async def cmd_list(message: Message, db: Database, translator: TranslationService, **_):
    lang = await _lang(db, message.from_user.id)
    schedules = await db.get_schedules(message.from_user.id)

    if not schedules:
        await message.answer(translator.get_message("msg_no_active_schedules", lang))
        return

    keys = [
        "msg_list_title", "msg_list_status_active", "msg_list_status_paused",
        "msg_list_id", "msg_list_status", "msg_list_target",
        "msg_list_message", "msg_list_schedule", "msg_list_use_manage",
    ]
    m = {k: translator.get_message(k, lang) for k in keys}

    text = f"{m['msg_list_title']}\n\n"
    for job in schedules:
        status = m["msg_list_status_paused"] if job["is_paused"] else m["msg_list_status_active"]
        desc = job["schedule_data"].get("description", "Unknown")
        text += (
            f"{m['msg_list_id']}{job['job_id']}`\n"
            f"{m['msg_list_status']}{status}\n"
            f"{m['msg_list_target']}{job['chat_id']}\n"
            f"{m['msg_list_message']}{job['message'][:50]}...\n"
            f"{m['msg_list_schedule']}{desc}`\n"
            "─────────────\n"
        )
    text += f"\n{m['msg_list_use_manage']}"
    await message.answer(text, reply_markup=kb.manage_button(translator, lang))


# ------------------------------------------------------------------
# /manage
# ------------------------------------------------------------------

@router.message(Command("manage"))
async def cmd_manage(message: Message, db: Database, translator: TranslationService, **_):
    lang = await _lang(db, message.from_user.id)
    schedules = await db.get_schedules(message.from_user.id)

    if not schedules:
        await message.answer(translator.get_message("msg_no_schedules_manage", lang))
        return

    for job in schedules:
        text = _build_job_text(job, translator, lang)
        markup = kb.job_manage_keyboard(translator, lang, job["job_id"], job["is_paused"])
        await message.answer(text, reply_markup=markup)


# ------------------------------------------------------------------
# Wizard – text messages while inside FSM
# ------------------------------------------------------------------

@router.message(StateFilter(ScheduleWizard.waiting_chat_id), F.text)
async def wizard_chat_id(message: Message, state: FSMContext, db: Database, translator: TranslationService, **_):
    lang = await _lang(db, message.from_user.id)
    target = str(message.chat.id) if message.text.lower() == "me" else message.text

    try:
        if str(target).lstrip("-").isdigit():
            await db.add_recent_chat_id(message.from_user.id, int(target))
    except Exception as e:
        logger.warning("Could not save recent chat_id: %s", e)

    await state.update_data(chat_id=target)
    await state.set_state(ScheduleWizard.waiting_message)
    await message.answer(translator.get_message("msg_schedule_step2", lang))


@router.message(StateFilter(ScheduleWizard.waiting_message), F.text)
async def wizard_message(message: Message, state: FSMContext, db: Database, translator: TranslationService, **_):
    lang = await _lang(db, message.from_user.id)
    await state.update_data(message_text=message.text)
    await state.set_state(ScheduleWizard.waiting_schedule)

    keys = [
        "msg_schedule_step3_title", "msg_schedule_examples",
        "msg_help_daily", "msg_help_every_minutes", "msg_help_every_hours",
        "msg_help_cron_monday", "msg_schedule_step3_hint",
    ]
    m = {k: translator.get_message(k, lang) for k in keys}
    text = (
        f"{m['msg_schedule_step3_title']}\n\n"
        f"{m['msg_schedule_examples']}\n"
        f"{m['msg_help_daily']}\n{m['msg_help_every_minutes']}\n"
        f"{m['msg_help_every_hours']}\n{m['msg_help_cron_monday']}\n\n"
        f"{m['msg_schedule_step3_hint']}"
    )
    await message.answer(text)


@router.message(StateFilter(ScheduleWizard.waiting_schedule), F.text)
async def wizard_schedule(
    message: Message,
    state: FSMContext,
    db: Database,
    translator: TranslationService,
    scheduler: SchedulerService,
    ai_service: AIService,
    **_,
):
    lang = await _lang(db, message.from_user.id)
    data = await state.get_data()
    user_id = message.from_user.id
    job_id = f"job_{user_id}_{int(datetime.now().timestamp())}"

    try:
        cron_expr = await ai_service.parse_schedule_to_cron(message.text.strip())
        schedule_data = scheduler.add_job(job_id, data["chat_id"], data["message_text"], cron_expr)

        await db.save_schedule(
            job_id=job_id,
            user_id=user_id,
            chat_id=data["chat_id"],
            message=data["message_text"],
            schedule_data=schedule_data,
            is_paused=False,
        )

        mk = {k: translator.get_message(k, lang) for k in [
            "msg_success_created", "msg_success_id", "msg_success_schedule", "msg_success_target",
        ]}
        text = (
            f"{mk['msg_success_created']}\n\n"
            f"{mk['msg_success_id']}{job_id}`\n"
            f"{mk['msg_success_schedule']}{schedule_data['description']}`\n"
            f"{mk['msg_success_target']}{data['chat_id']}\n"
        )
        await message.answer(text, reply_markup=kb.success_keyboard(translator, lang, job_id))
        await state.clear()

    except Exception as e:
        logger.error("Error creating schedule: %s", e)
        # keep user in schedule step so they can retry
        mk = {k: translator.get_message(k, lang) for k in [
            "msg_error_create", "msg_error_retry", "msg_error_restart",
        ]}
        error_text = (
            f"{mk['msg_error_create']}{e}\n\n"
            f"{mk['msg_error_retry']}\n"
            f"{mk['msg_error_restart']}"
        )
        await message.answer(error_text, reply_markup=kb.restart_button(translator, lang))


# ------------------------------------------------------------------
# Shared helpers
# ------------------------------------------------------------------

def _build_job_text(job: dict, tr: TranslationService, lang: str) -> str:
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

