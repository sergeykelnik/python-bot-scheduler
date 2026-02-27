# Telegram Scheduled Messages Bot

A Telegram bot for scheduling messages, built with **aiogram 3.25.0**, featuring persistent storage, internationalization, and AI-powered natural language parsing.

## Features

- **Smart Scheduling**: Use natural language (e.g., "every Monday at 9am") or standard cron syntax.
- **Multilingual**: Supports English and Russian.
- **Persistent Storage**: Uses SQLite to save schedules between restarts.
- **Interactive Management**: Manage your schedules via inline buttons (Pause, Resume, Delete).
- **Fully Async**: Built on aiogram 3.x, aiosqlite, and APScheduler's AsyncIOScheduler.

## Quick Start

### 1. Prerequisites
- Python 3.10+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Groq API Key (optional, for AI natural language parsing)

### 2. Installation

```bash
git clone https://github.com/sergeykelnik/python-bot-scheduler.git
cd python-bot-scheduler

python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GROQ_API_KEY=your_groq_api_key
LOG_LEVEL=INFO
```

### 4. Usage

```bash
python main.py
```

### 5. Bot Commands

- `/start` - Main menu and language selection.
- `/schedule` - Create a new schedule wizard.
- `/list` - View your active schedules.
- `/manage` - Manage (Pause/Resume/Delete) schedules.
- `/help` - Show help and examples.

## Project Structure

```
├── main.py              # Entry point
├── src/bot/             # Bot application
│   ├── bot.py           # Bot & Dispatcher setup, lifecycle
│   ├── handlers.py      # Command handlers + FSM wizard
│   ├── callbacks.py     # Inline button callback handlers
│   ├── helpers.py       # Shared text builders & utilities
│   ├── keyboards.py     # Inline keyboard builders
│   ├── states.py        # FSM states (ScheduleWizard)
│   ├── config.py        # Configuration (env vars)
│   ├── database.py      # Async SQLite (aiosqlite)
│   ├── scheduler_service.py  # AsyncIOScheduler + cron
│   ├── ai_service.py    # Groq AI for NLP → cron
│   └── translation_service.py  # i18n from locales/
├── locales/             # Translation files (en.json, ru.json)
├── tests/               # Smoke tests
└── schedules.db         # SQLite database
```

## License

MIT
