"""
Entry point for the Telegram Bot Scheduler.
"""

import asyncio
import sys

from src.bot.config import BOT_TOKEN


async def main() -> None:
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("ERROR: Please provide a valid bot token!")
        print("Option 1: Set environment variable")
        print("  $env:TELEGRAM_BOT_TOKEN='your_token_here'")
        print("Option 2: Replace 'YOUR_BOT_TOKEN_HERE' in .env file")
        sys.exit(1)

    from src.bot.bot import build_bot_and_dispatcher

    bot, dp = build_bot_and_dispatcher()
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass