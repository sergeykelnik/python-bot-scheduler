"""
Main entry point for the Python Bot Scheduler.
"""

import os
import logging
from src.core.config import BOT_TOKEN
from src.bot.telegram_bot import TelegramBot

# logger configuration is handled in src.core.config and src.bot.telegram_bot

if __name__ == '__main__':
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("ERROR: Please provide a valid bot token!")
        print("Option 1: Set environment variable")
        print("  $env:TELEGRAM_BOT_TOKEN='your_token_here'")
        print("Option 2: Replace 'YOUR_BOT_TOKEN_HERE' in .env file")
        exit(1)
    
    # Create and start the bot
    bot = TelegramBot(BOT_TOKEN)
    bot.start_polling()
