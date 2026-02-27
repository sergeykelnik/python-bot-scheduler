"""
Callback-query handlers (aiogram Router).
"""

import asyncio
import logging

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from src.bot2.states import ScheduleWizard
from src.bot2.database import Database
from src.bot2.translation_service import TranslationService
from src.bot2.scheduler_service import SchedulerService
from src.bot2 import keyboards as kb
from src.bot2.handlers import _build_job_text

logger = logging.getLogger(__name__)

router = Router(name="callbacks")


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

async def _lang(db: Database, user_id: int) -> str:
    try:
        return await db.get_user_language(user_id)
    except Exception:
        return "ru"


async def _get_job(db: Database, job_id: str, user_id: int):
    jobs = await db.get_schedules(user_id)
    for j in jobs:
        if j["job_id"] == job_id:
            return j
    return None


# ------------------------------------------------------------------
# Language change   lang:en / lang:ru
# ------------------------------------------------------------------

@router.callback_query(F.data.startswith("lang:"))
async def cb_language(
    cq: CallbackQuery,
    bot: Bot,
    db: Database,
    translator: TranslationService,
    **_,
):
    new_lang = cq.data.split(":")[1]
    await asyncio.sleep(0.1)

    # Set menu commands for the new language
    from aiogram.types import BotCommand
    commands = [
        BotCommand(command="start", description=translator.get_message("cmd_start", new_lang)),
        BotCommand(command="help", description=translator.get_message("cmd_help", new_lang)),
        BotCommand(command="schedule", description=translator.get_message("cmd_schedule", new_lang)),
        BotCommand(command="list", description=translator.get_message("cmd_list", new_lang)),
        BotCommand(command="manage", description=translator.get_message("cmd_manage", new_lang)),
    ]
    await bot.set_my_commands(commands, language_code=new_lang)

    await db.set_user_language(cq.from_user.id, new_lang)

    msg = translator.get_message("msg_callback_lang_changed", new_lang)
    await cq.answer(f"{msg}{new_lang.upper()}")

    # Refresh /start view
    chat_id = cq.message.chat.id
    title = translator.get_message("msg_start_title", new_lang)
    desc = translator.get_message("msg_start_description", new_lang)
    await bot.send_message(chat_id, f"{title}\n\n{desc}", reply_markup=kb.start_keyboard(translator, new_lang))


# ------------------------------------------------------------------
# Schedule wizard buttons
# ------------------------------------------------------------------

@router.callback_query(F.data == "schedule:me")
async def cb_schedule_me(
    cq: CallbackQuery,
    state: FSMContext,
    db: Database,
    translator: TranslationService,
    **_,
):
    lang = await _lang(db, cq.from_user.id)
    await state.update_data(chat_id=str(cq.message.chat.id))
    await state.set_state(ScheduleWizard.waiting_message)
    await cq.answer()
    await cq.message.answer(translator.get_message("msg_schedule_step2", lang))


@router.callback_query(F.data == "schedule:saved_contacts")
async def cb_saved_contacts(
    cq: CallbackQuery,
    db: Database,
    translator: TranslationService,
    **_,
):
    lang = await _lang(db, cq.from_user.id)
    await cq.answer()
    contacts = await db.get_recent_chat_ids(cq.from_user.id)
    if not contacts:
        await cq.message.answer(translator.get_message("msg_no_saved_contacts", lang))
        return
    msg = translator.get_message("msg_select_saved_contact", lang)
    await cq.message.answer(msg, reply_markup=kb.saved_contacts_keyboard(translator, lang, contacts))


@router.callback_query(F.data.startswith("schedule:select_contact:"))
async def cb_select_contact(
    cq: CallbackQuery,
    state: FSMContext,
    db: Database,
    translator: TranslationService,
    **_,
):
    lang = await _lang(db, cq.from_user.id)
    try:
        contact_id = int(cq.data.split(":")[2])
    except (ValueError, IndexError):
        await cq.answer()
        return

    await state.update_data(chat_id=str(contact_id))
    await state.set_state(ScheduleWizard.waiting_message)
    await cq.answer()
    await cq.message.answer(translator.get_message("msg_schedule_step2", lang))


# ------------------------------------------------------------------
# Main-menu navigation   cmd:schedule / cmd:list / cmd:manage / cmd:help
# ------------------------------------------------------------------

@router.callback_query(F.data.startswith("cmd:"))
async def cb_cmd(
    cq: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    db: Database,
    translator: TranslationService,
    scheduler: SchedulerService,
    ai_service,
    **_,
):
    cmd = cq.data.split(":")[1]
    await cq.answer()

    chat_id = cq.message.chat.id
    user_id = cq.from_user.id
    lang = await _lang(db, user_id)

    if cmd == "schedule":
        await state.set_state(ScheduleWizard.waiting_chat_id)
        title = translator.get_message("msg_schedule_title", lang)
        step1 = translator.get_message("msg_schedule_step1", lang)
        hint = translator.get_message("msg_schedule_step1_hint", lang)
        recent = await db.get_recent_chat_ids(user_id)
        markup = kb.schedule_step1_keyboard(translator, lang, has_recent_contacts=bool(recent))
        await bot.send_message(chat_id, f"{title}\n\n{step1}\n{hint}", reply_markup=markup)

    elif cmd == "list":
        schedules = await db.get_schedules(user_id)
        if not schedules:
            await bot.send_message(chat_id, translator.get_message("msg_no_active_schedules", lang))
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
        await bot.send_message(chat_id, text, reply_markup=kb.manage_button(translator, lang))

    elif cmd == "manage":
        schedules = await db.get_schedules(user_id)
        if not schedules:
            await bot.send_message(chat_id, translator.get_message("msg_no_schedules_manage", lang))
            return
        for job in schedules:
            text = _build_job_text(job, translator, lang)
            markup = kb.job_manage_keyboard(translator, lang, job["job_id"], job["is_paused"])
            await bot.send_message(chat_id, text, reply_markup=markup)

    elif cmd == "help":
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
        await bot.send_message(chat_id, text, reply_markup=kb.help_keyboard(translator, lang))


# ------------------------------------------------------------------
# Manage actions   manage:pause:<id> / manage:resume:<id> / manage:delete:<id>
# ------------------------------------------------------------------

@router.callback_query(F.data.startswith("manage:"))
async def cb_manage_action(
    cq: CallbackQuery,
    db: Database,
    translator: TranslationService,
    scheduler: SchedulerService,
    **_,
):
    parts = cq.data.split(":")
    if len(parts) != 3:
        await cq.answer()
        return

    subaction, job_id = parts[1], parts[2]
    user_id = cq.from_user.id
    lang = await _lang(db, user_id)

    job = await _get_job(db, job_id, user_id)
    if not job:
        await cq.answer(translator.get_message("msg_callback_not_found", lang), show_alert=True)
        return

    if subaction == "pause":
        if scheduler.pause_job(job_id):
            await db.update_schedule_pause_status(job_id, True)
            job["is_paused"] = True
            text = _build_job_text(job, translator, lang)
            markup = kb.job_manage_keyboard(translator, lang, job_id, True)
            await cq.message.edit_text(text, reply_markup=markup)
            await cq.answer(translator.get_message("msg_callback_paused", lang))
        else:
            await cq.answer(translator.get_message("msg_callback_pause_error", lang), show_alert=True)

    elif subaction == "resume":
        sd = job["schedule_data"]
        if scheduler.resume_job(job_id, sd["expression"], job["chat_id"], job["message"]):
            await db.update_schedule_pause_status(job_id, False)
            job["is_paused"] = False
            text = _build_job_text(job, translator, lang)
            markup = kb.job_manage_keyboard(translator, lang, job_id, False)
            await cq.message.edit_text(text, reply_markup=markup)
            await cq.answer(translator.get_message("msg_callback_resumed", lang))
        else:
            await cq.answer(translator.get_message("msg_callback_resume_error", lang), show_alert=True)

    elif subaction == "delete":
        confirm_prefix = translator.get_message("msg_confirm_delete", lang)
        confirm_text = f"{confirm_prefix}{job_id}`\n\n" + _build_job_text(job, translator, lang)
        await cq.message.edit_text(
            confirm_text,
            reply_markup=kb.confirm_delete_keyboard(translator, lang, job_id),
        )
        await cq.answer()


# ------------------------------------------------------------------
# Delete confirmation / cancellation
# ------------------------------------------------------------------

@router.callback_query(F.data.startswith("confirm_delete:"))
async def cb_confirm_delete(
    cq: CallbackQuery,
    db: Database,
    translator: TranslationService,
    scheduler: SchedulerService,
    **_,
):
    job_id = cq.data.split(":")[1]
    lang = await _lang(db, cq.from_user.id)

    scheduler.delete_job(job_id)
    await db.delete_schedule(job_id)

    await cq.answer(translator.get_message("msg_callback_deleted", lang))

    lbl_id = translator.get_message("msg_job_id", lang)
    lbl_st = translator.get_message("msg_job_status", lang)
    deleted_status = translator.get_message("msg_list_status_deleted", lang)
    text = f"{lbl_id}{job_id}`\n{lbl_st}{deleted_status}\n"
    await cq.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[]))


@router.callback_query(F.data.startswith("cancel_delete:"))
async def cb_cancel_delete(
    cq: CallbackQuery,
    db: Database,
    translator: TranslationService,
    **_,
):
    job_id = cq.data.split(":")[1]
    user_id = cq.from_user.id
    lang = await _lang(db, user_id)

    job = await _get_job(db, job_id, user_id)
    if not job:
        await cq.answer()
        return

    text = _build_job_text(job, translator, lang)
    markup = kb.job_manage_keyboard(translator, lang, job_id, job["is_paused"])
    await cq.message.edit_text(text, reply_markup=markup)
    await cq.answer(translator.get_message("msg_callback_cancelled", lang))

