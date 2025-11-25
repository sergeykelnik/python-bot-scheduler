# Telegram Scheduled Messages Bot

A Python-based Telegram bot for scheduling messages with persistent storage.

## Features

- Schedule messages (daily, interval, cron)
- Pause/resume/delete schedules
- SQLite database for persistence
- Interactive management interface
- AI-based schedule parsing (natural language)
- 115+ unit tests with 88% coverage

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
```

## Running Tests

```bash
# Run all tests
pytest tests

# Run with coverage report
pytest tests --cov=. --cov-report=html

# Run specific test file
pytest tests/test_bot.py -v
```

See [QUICK_TEST_GUIDE.md](QUICK_TEST_GUIDE.md) for more testing options.

## Deployment

### Docker Deployment

#### Using Docker Compose
```bash
# Build and run with Docker Compose
docker-compose up -d
```

Create a `docker-compose.yml`:
```yaml
version: '3.8'
services:
  telegram-bot:
    build: .
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - LOG_LEVEL=INFO
    volumes:
      - ./schedules.db:/app/schedules.db
    restart: unless-stopped
```

#### Manual Docker Build
```bash
# Build image
docker build -t telegram-bot-scheduler .

# Run container
docker run -d \
  --name telegram-bot \
  -e TELEGRAM_BOT_TOKEN=your_token_here \
  -v $(pwd)/schedules.db:/app/schedules.db \
  --restart unless-stopped \
  telegram-bot-scheduler
```

Create a `Dockerfile`:
```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

### Cloud Deployment

#### Heroku
```bash
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Set environment variable
heroku config:set TELEGRAM_BOT_TOKEN=your_token_here

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

Create a `Procfile`:
```
worker: python bot.py
```

#### Railway.app
1. Connect your GitHub repository to Railway
2. Add environment variable: `TELEGRAM_BOT_TOKEN`
3. Set start command: `python bot.py`
4. Deploy

#### AWS EC2
```bash
# SSH into instance
ssh -i your-key.pem ec2-user@your-instance-ip

# Install Python and dependencies
sudo yum update -y
sudo yum install python3 python3-pip -y

# Clone and setup
git clone https://github.com/sergeykelnik/python-bot-scheduler.git
cd python-bot-scheduler
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up environment
echo "TELEGRAM_BOT_TOKEN=your_token_here" > .env

# Run with systemd (keep running)
sudo systemctl start telegram-bot
```

Create `/etc/systemd/system/telegram-bot.service`:
```ini
[Unit]
Description=Telegram Scheduled Messages Bot
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/python-bot-scheduler
Environment="PATH=/home/ec2-user/python-bot-scheduler/venv/bin"
EnvironmentFile=/home/ec2-user/python-bot-scheduler/.env
ExecStart=/home/ec2-user/python-bot-scheduler/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

#### Render
1. Connect GitHub repo to Render
2. Create new "Web Service"
3. Set environment variables:
   - `TELEGRAM_BOT_TOKEN=your_token`
4. Build command: `pip install -r requirements.txt`
5. Start command: `python bot.py`
6. Deploy

### VPS/Self-Hosted

#### Using systemd (Ubuntu/Debian)
```bash
# Clone repository
git clone https://github.com/sergeykelnik/python-bot-scheduler.git
cd python-bot-scheduler

# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env
echo "TELEGRAM_BOT_TOKEN=your_token_here" > .env

# Create systemd service
sudo tee /etc/systemd/system/telegram-bot.service > /dev/null <<EOF
[Unit]
Description=Telegram Scheduled Messages Bot
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
EnvironmentFile=$(pwd)/.env
ExecStart=$(pwd)/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# Check status
sudo systemctl status telegram-bot

# View logs
sudo journalctl -u telegram-bot -f
```

#### Using supervisor
```bash
# Install supervisor
sudo apt-get install supervisor

# Create config
sudo tee /etc/supervisor/conf.d/telegram-bot.conf > /dev/null <<EOF
[program:telegram-bot]
directory=/home/user/python-bot-scheduler
command=/home/user/python-bot-scheduler/venv/bin/python bot.py
user=user
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/telegram-bot.log
environment=TELEGRAM_BOT_TOKEN="your_token_here"
EOF

# Start
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start telegram-bot
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token from @BotFather | Yes |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |
| `SCHEDULES_DB_PATH` | Path to SQLite database file | No (default: schedules.db) |
| `GROQ_API_KEY` | Groq API key for AI schedule parsing | No |

## Database

The bot uses SQLite for persistence. The database file (`schedules.db`) is created automatically.

For production deployments, consider:
- Regular backups of the database
- Using volume mounts (Docker) to persist data
- Monitoring database file size

## Monitoring and Logging

Check logs based on your deployment method:

**Local/VPS:**
```bash
tail -f logs.txt  # if redirected to file
```

**Docker:**
```bash
docker logs -f telegram-bot
```

**Heroku:**
```bash
heroku logs --tail
```

**systemd:**
```bash
sudo journalctl -u telegram-bot -f
```

## Troubleshooting

**Bot not responding:**
1. Verify `TELEGRAM_BOT_TOKEN` is correct
2. Check logs for errors
3. Ensure internet connection is stable
4. Verify firewall allows outbound HTTPS

**Schedules not executing:**
1. Check bot is running: `ps aux | grep bot.py`
2. Verify timezone settings in `config.py`
3. Check database file is writable
4. Review logs for parsing errors

**High memory usage:**
1. Check number of active schedules
2. Monitor database file size
3. Restart bot if needed

## License

MIT
