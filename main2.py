"""
Entry point for the aiogram-based bot (bot2).
"""

import asyncio
import sys

from src.bot2.config import BOT_TOKEN


async def main() -> None:
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("ERROR: Please provide a valid bot token!")
        print("Option 1: Set environment variable")
        print("  $env:TELEGRAM_BOT_TOKEN='your_token_here'")
        print("Option 2: Replace 'YOUR_BOT_TOKEN_HERE' in .env file")
        sys.exit(1)

    # Import here so config (and logging) is set up first
    from src.bot2.bot import build_bot_and_dispatcher

    bot, dp = build_bot_and_dispatcher()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

