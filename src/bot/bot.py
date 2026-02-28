"""
Bot & Dispatcher setup, startup / shutdown lifecycle.
"""

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from src.bot.database import Database
from src.bot.translation_service import TranslationService
from src.bot.scheduler_service import SchedulerService
from src.bot.ai_service import AIService
from src.bot.handlers import router as handlers_router
from src.bot.callbacks import router as callbacks_router

logger = logging.getLogger(__name__)


def build_bot_and_dispatcher():
    """Construct and return (Bot, Dispatcher) with all services wired."""

    from src.bot.config import BOT_TOKEN

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )

    async def send_scheduled_message(chat_id: str, message: str) -> None:
        """Callback invoked by the scheduler when a job fires."""
        logger.info("Sending scheduled message to %s", chat_id)
        await bot.send_message(chat_id, message)

    dp = Dispatcher(storage=MemoryStorage())

    # --- Services ---
    db = Database()
    translator = TranslationService()
    ai_service = AIService()
    scheduler = SchedulerService(callback_func=send_scheduled_message)

    dp["db"] = db
    dp["translator"] = translator
    dp["ai_service"] = ai_service
    dp["scheduler"] = scheduler

    # --- Routers ---
    dp.include_router(handlers_router)
    dp.include_router(callbacks_router)

    # --- Lifecycle hooks ---
    @dp.startup()
    async def on_startup() -> None:
        logger.info("Bot starting up…")
        await db.init()

        # Set menu commands for every available language
        for lang in translator.available_languages():
            commands = [
                BotCommand(command="start", description=translator.get_message("cmd_start", lang)),
                BotCommand(command="help", description=translator.get_message("cmd_help", lang)),
                BotCommand(command="schedule", description=translator.get_message("cmd_schedule", lang)),
                BotCommand(command="list", description=translator.get_message("cmd_list", lang)),
                BotCommand(command="manage", description=translator.get_message("cmd_manage", lang)),
            ]
            await bot.set_my_commands(commands, language_code=lang)

        # Restore persisted schedules
        all_schedules = await db.get_schedules()
        logger.info("Loading %d schedules from database…", len(all_schedules))
        for s in all_schedules:
            if not s["is_paused"]:
                try:
                    scheduler.add_job(
                        s["job_id"],
                        s["chat_id"],
                        s["message"],
                        s["schedule_data"]["expression"],
                    )
                except Exception as e:
                    logger.error("Failed to restore job %s: %s", s["job_id"], e)

        scheduler.start()
        logger.info("Bot is ready.")

    @dp.shutdown()
    async def on_shutdown() -> None:
        logger.info("Bot shutting down…")
        scheduler.shutdown()

    return bot, dp

