# Telegram Bot Scheduler - Deployment Guide

## Quick Deployment

### Ubuntu/Debian Server

1. Copy all files to your server
2. Run the deployment script:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

The script will automatically install Docker if not present.

## What the deployment script does:

1. ✅ Checks if Docker is installed (offers to install on Ubuntu)
2. ✅ Creates `.env` file with your API keys (if not exists)
3. ✅ Creates empty `schedules.db` file (if not exists)
4. ✅ Builds the Docker image
5. ✅ Starts the bot in detached mode

## Using a different schedules.db file

Simply replace the `schedules.db` file in the deployment directory before running the script, or after deployment:

```bash
# Stop the bot
docker-compose down

# Replace the database file
cp /path/to/your/schedules.db ./schedules.db

# Restart the bot
docker-compose up -d
```

## Useful Commands

```bash
# View logs in real-time
docker-compose logs -f

# Stop the bot
docker-compose down

# Restart the bot
docker-compose restart

# Check bot status
docker-compose ps

# Update the bot (after code changes)
docker-compose down
docker-compose build
docker-compose up -d
```

## File Structure Required

```
deployment-folder/
├── deploy.sh
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── main.py
├── .env (created automatically or manually)
├── schedules.db (created automatically or upload your own)
├── src/
├── locales/
└── ... (all other project files)
```

## Prerequisites

- Ubuntu/Debian Linux server
- Internet connection to download Docker and dependencies
- Sudo access for Docker installation

## Environment Variables

The `.env` file should contain:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
GROQ_API_KEY=your_groq_api_key_here
```

## Troubleshooting

**Bot not starting:**
```bash
docker-compose logs
```

**Permission issues on Linux:**
```bash
sudo chmod +x deploy.sh
sudo ./deploy.sh
```

**Port already in use:**
The bot doesn't expose any ports by default, so this shouldn't be an issue.

**Database file not found:**
The script will create an empty `schedules.db` if none exists. To use your own database, place it in the same directory as the `docker-compose.yml` file.
