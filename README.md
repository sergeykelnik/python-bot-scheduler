# Telegram Scheduled Messages Bot

A Python-based Telegram bot for scheduling messages with persistent storage.

## Features

- Schedule messages (daily, interval, cron)
- Pause/resume/delete schedules
- SQLite database for persistence
- Interactive management interface

## Quick Start

### 1. Get Bot Token
Create a bot via [@BotFather](https://t.me/BotFather) and get your token.

### 2. Local Setup
```bash
git clone https://github.com/sergeykelnik/python-bot-scheduler.git
cd python-bot-scheduler

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file with your token
echo "TELEGRAM_BOT_TOKEN=your_token_here" > .env

python bot.py