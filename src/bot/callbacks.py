"""
Callback-query handlers (aiogram Router).
"""

import asyncio
import logging

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommand, CallbackQuery, InlineKeyboardMarkup

from src.bot.states import ScheduleWizard
from src.bot.database import Database
from src.bot.translation_service import TranslationService
from src.bot.scheduler_service import SchedulerService
from src.bot.helpers import get_lang, build_help_text, build_list_text, build_job_text, validate_chat_id
from src.bot import keyboards as kb

logger = logging.getLogger(__name__)

router = Router(name="callbacks")


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

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
    lang = await get_lang(db, cq.from_user.id)
    await state.update_data(chat_id=str(cq.message.chat.id))
    await state.set_state(ScheduleWizard.waiting_message)
    await cq.answer()
    await cq.message.answer(translator.get_message("msg_schedule_step2", lang))


@router.callback_query(F.data == "schedule:saved_contacts")
async def cb_saved_contacts(
    cq: CallbackQuery,
    bot: Bot,
    db: Database,
    translator: TranslationService,
    **_,
):
    lang = await get_lang(db, cq.from_user.id)
    await cq.answer()
    contacts = await db.get_recent_chat_ids(cq.from_user.id)

    # Filter out unreachable contacts
    reachable = []
    for c in contacts:
        if await validate_chat_id(bot, str(c)):
            reachable.append(c)

    if not reachable:
        await cq.message.answer(translator.get_message("msg_no_saved_contacts", lang))
        # Re-present step 1 without the saved contacts button
        title = translator.get_message("msg_schedule_title", lang)
        step1 = translator.get_message("msg_schedule_step1", lang)
        hint = translator.get_message("msg_schedule_step1_hint", lang)
        markup = kb.schedule_step1_keyboard(translator, lang, has_recent_contacts=False)
        await cq.message.answer(f"{title}\n\n{step1}\n{hint}", reply_markup=markup)
        return
    msg = translator.get_message("msg_select_saved_contact", lang)
    await cq.message.answer(msg, reply_markup=kb.saved_contacts_keyboard(translator, lang, reachable))


@router.callback_query(F.data.startswith("schedule:select_contact:"))
async def cb_select_contact(
    cq: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    db: Database,
    translator: TranslationService,
    **_,
):
    lang = await get_lang(db, cq.from_user.id)
    try:
        contact_id = int(cq.data.split(":")[2])
    except (ValueError, IndexError):
        await cq.answer()
        return

    if not await validate_chat_id(bot, str(contact_id)):
        await cq.answer()
        msg = translator.get_message("msg_chat_unreachable", lang).replace("{chat_id}", str(contact_id))
        await cq.message.answer(msg)
        # Re-present step 1
        title = translator.get_message("msg_schedule_title", lang)
        step1 = translator.get_message("msg_schedule_step1", lang)
        hint = translator.get_message("msg_schedule_step1_hint", lang)
        recent = await db.get_recent_chat_ids(cq.from_user.id)
        markup = kb.schedule_step1_keyboard(translator, lang, has_recent_contacts=bool(recent))
        await cq.message.answer(f"{title}\n\n{step1}\n{hint}", reply_markup=markup)
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
    **_,
):
    cmd = cq.data.split(":")[1]
    await cq.answer()

    chat_id = cq.message.chat.id
    user_id = cq.from_user.id
    lang = await get_lang(db, user_id)

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
        await bot.send_message(chat_id, build_list_text(schedules, translator, lang), reply_markup=kb.manage_button(translator, lang))

    elif cmd == "manage":
        schedules = await db.get_schedules(user_id)
        if not schedules:
            await bot.send_message(chat_id, translator.get_message("msg_no_schedules_manage", lang))
            return
        for job in schedules:
            await bot.send_message(chat_id, build_job_text(job, translator, lang),
                                   reply_markup=kb.job_manage_keyboard(translator, lang, job["job_id"], job["is_paused"]))

    elif cmd == "help":
        await bot.send_message(chat_id, build_help_text(translator, lang), reply_markup=kb.help_keyboard(translator, lang))


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
    lang = await get_lang(db, user_id)

    job = await _get_job(db, job_id, user_id)
    if not job:
        await cq.answer(translator.get_message("msg_callback_not_found", lang), show_alert=True)
        return

    if subaction == "pause":
        if scheduler.pause_job(job_id):
            await db.update_schedule_pause_status(job_id, True)
            job["is_paused"] = True
            await cq.message.edit_text(
                build_job_text(job, translator, lang),
                reply_markup=kb.job_manage_keyboard(translator, lang, job_id, True),
            )
            await cq.answer(translator.get_message("msg_callback_paused", lang))
        else:
            await cq.answer(translator.get_message("msg_callback_pause_error", lang), show_alert=True)

    elif subaction == "resume":
        sd = job["schedule_data"]
        if scheduler.resume_job(job_id, sd["expression"], job["chat_id"], job["message"]):
            await db.update_schedule_pause_status(job_id, False)
            job["is_paused"] = False
            await cq.message.edit_text(
                build_job_text(job, translator, lang),
                reply_markup=kb.job_manage_keyboard(translator, lang, job_id, False),
            )
            await cq.answer(translator.get_message("msg_callback_resumed", lang))
        else:
            await cq.answer(translator.get_message("msg_callback_resume_error", lang), show_alert=True)

    elif subaction == "delete":
        confirm_prefix = translator.get_message("msg_confirm_delete", lang)
        confirm_text = f"{confirm_prefix}{job_id}`\n\n" + build_job_text(job, translator, lang)
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
    lang = await get_lang(db, cq.from_user.id)

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
    lang = await get_lang(db, user_id)

    job = await _get_job(db, job_id, user_id)
    if not job:
        await cq.answer()
        return

    await cq.message.edit_text(
        build_job_text(job, translator, lang),
        reply_markup=kb.job_manage_keyboard(translator, lang, job_id, job["is_paused"]),
    )
    await cq.answer(translator.get_message("msg_callback_cancelled", lang))

