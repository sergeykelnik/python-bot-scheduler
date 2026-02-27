"""
Command & text-message handlers (aiogram Router).
"""

import logging
from datetime import datetime

from aiogram import Bot, Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.bot.states import ScheduleWizard
from src.bot.database import Database
from src.bot.translation_service import TranslationService
from src.bot.scheduler_service import SchedulerService
from src.bot.ai_service import AIService
from src.bot.helpers import get_lang, build_help_text, build_list_text, build_job_text, validate_chat_id
from src.bot import keyboards as kb

logger = logging.getLogger(__name__)

router = Router(name="handlers")


# ------------------------------------------------------------------
# /start
# ------------------------------------------------------------------

@router.message(Command("start"))
async def cmd_start(message: Message, db: Database, translator: TranslationService, **_):
    lang = await get_lang(db, message.from_user.id)
    title = translator.get_message("msg_start_title", lang)
    desc = translator.get_message("msg_start_description", lang)
    await message.answer(f"{title}\n\n{desc}", reply_markup=kb.start_keyboard(translator, lang))


# ------------------------------------------------------------------
# /help
# ------------------------------------------------------------------

@router.message(Command("help"))
async def cmd_help(message: Message, db: Database, translator: TranslationService, **_):
    lang = await get_lang(db, message.from_user.id)
    await message.answer(build_help_text(translator, lang), reply_markup=kb.help_keyboard(translator, lang))


# ------------------------------------------------------------------
# /schedule  – enter the wizard
# ------------------------------------------------------------------

@router.message(Command("schedule"))
async def cmd_schedule(message: Message, state: FSMContext, db: Database, translator: TranslationService, **_):
    lang = await get_lang(db, message.from_user.id)
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
    lang = await get_lang(db, message.from_user.id)
    schedules = await db.get_schedules(message.from_user.id)

    if not schedules:
        await message.answer(translator.get_message("msg_no_active_schedules", lang))
        return

    await message.answer(build_list_text(schedules, translator, lang), reply_markup=kb.manage_button(translator, lang))


# ------------------------------------------------------------------
# /manage
# ------------------------------------------------------------------

@router.message(Command("manage"))
async def cmd_manage(message: Message, db: Database, translator: TranslationService, **_):
    lang = await get_lang(db, message.from_user.id)
    schedules = await db.get_schedules(message.from_user.id)

    if not schedules:
        await message.answer(translator.get_message("msg_no_schedules_manage", lang))
        return

    for job in schedules:
        text = build_job_text(job, translator, lang)
        markup = kb.job_manage_keyboard(translator, lang, job["job_id"], job["is_paused"])
        await message.answer(text, reply_markup=markup)


# ------------------------------------------------------------------
# Wizard – text messages while inside FSM
# ------------------------------------------------------------------

@router.message(StateFilter(ScheduleWizard.waiting_chat_id), F.text)
async def wizard_chat_id(message: Message, bot: Bot, state: FSMContext, db: Database, translator: TranslationService, **_):
    lang = await get_lang(db, message.from_user.id)
    target = str(message.chat.id) if message.text.lower() == "me" else message.text

    # Validate the bot can reach this chat
    if not await validate_chat_id(bot, target):
        msg = translator.get_message("msg_chat_unreachable", lang).replace("{chat_id}", target)
        await message.answer(msg)
        return  # Stay in waiting_chat_id state so user can retry

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
    lang = await get_lang(db, message.from_user.id)
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
    lang = await get_lang(db, message.from_user.id)
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
        mk = {k: translator.get_message(k, lang) for k in [
            "msg_error_create", "msg_error_retry", "msg_error_restart",
        ]}
        error_text = (
            f"{mk['msg_error_create']}{e}\n\n"
            f"{mk['msg_error_retry']}\n"
            f"{mk['msg_error_restart']}"
        )
        await message.answer(error_text, reply_markup=kb.restart_button(translator, lang))
