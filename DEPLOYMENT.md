# Deployment

## Quick Start

```bash
git clone https://github.com/sergeykelnik/python-bot-scheduler.git
cd python-bot-scheduler
chmod +x deploy.sh
./deploy.sh
```

The script installs Docker (if needed), creates `.env` and `schedules.db`, builds the image, and starts the bot.

## Environment Variables

Create `.env`:

```env
TELEGRAM_BOT_TOKEN=your_token
GROQ_API_KEY=your_key
```

## Common Commands

```bash
docker compose logs -f      # View logs
docker compose restart      # Restart
docker compose down         # Stop
docker compose down && docker compose build && docker compose up -d  # Rebuild
```
