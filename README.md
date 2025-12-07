# Telegram Scheduled Messages Bot

A Python-based Telegram bot for scheduling messages with persistent storage, internationalization, and natural language parsing.

## Features

- **Smart Scheduling**: Use natural language (e.g., "every Monday at 9am") or standard cron syntax.
- **Multilingual**: Supports English and Russian.
- **Persistent Storage**: Uses SQLite to save schedules between restarts.
- **Interactive Management**: Manage your schedules via inline buttons (Pause, Resume, Delete).

## Quick Start

### 1. Prerequisites
- Python 3.10+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Groq API Key (optional, for AI natural language parsing)

### 2. Installation

Clone the repository and install dependencies:

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

Run the bot:

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

- `main.py` - Entry point.
- `src/`
  - `bot/` - Telegram bot logic and handlers.
  - `core/` - Configuration and database.
  - `services/` - Business logic (Scheduler, AI, Translation).

## License

MIT
