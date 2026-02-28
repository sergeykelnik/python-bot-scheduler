# Telegram Scheduled Messages Bot

Async Telegram bot for scheduling messages with natural language or cron syntax. Built with aiogram 3, aiosqlite, APScheduler, and Groq AI.

## Setup

```bash
pip install -r requirements.txt
```

Create `.env`:

```env
TELEGRAM_BOT_TOKEN=your_token
GROQ_API_KEY=your_key
```

Run:

```bash
python main.py
```

## Commands

| Command     | Description                        |
|-------------|------------------------------------|
| `/start`    | Main menu & language selection     |
| `/schedule` | Create a new scheduled message     |
| `/list`     | View active schedules              |
| `/manage`   | Pause / Resume / Delete schedules  |
| `/help`     | Help & cron examples               |

## Key Features

- Natural language → cron via Groq AI
- English / Russian localization
- Persistent SQLite storage
- Inline button management (pause, resume, delete)
