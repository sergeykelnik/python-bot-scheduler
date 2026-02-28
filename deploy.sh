#!/bin/bash
set -e

echo "=== Telegram Bot Scheduler Deployment ==="

# Install Docker if missing
if ! command -v docker &> /dev/null; then
    read -p "Docker not found. Install now? (y/n): " choice
    if [[ $choice =~ ^[Yy]$ ]]; then
        echo "Installing Docker..."
        curl -fsSL https://get.docker.com | sudo sh
        sudo systemctl enable --now docker
        sudo usermod -aG docker "$USER"
        echo "Docker installed. Log out and back in, then re-run this script."
        exit 0
    else
        echo "Aborted. Install Docker manually: https://docs.docker.com/engine/install/"
        exit 1
    fi
fi

if ! docker compose version &> /dev/null; then
    echo "Docker Compose plugin not found. Please install it: https://docs.docker.com/compose/install/"
    exit 1
fi

# Create .env if missing
if [ ! -f .env ]; then
    read -p "Telegram Bot Token: " BOT_TOKEN
    read -p "Groq API Key: " GROQ_KEY
    cat > .env <<EOF
TELEGRAM_BOT_TOKEN=${BOT_TOKEN}
GROQ_API_KEY=${GROQ_KEY}
EOF
    echo ".env created."
fi

# Create DB if missing
[ ! -f schedules.db ] && touch schedules.db

# Deploy
docker compose down 2>/dev/null || true
docker compose build
docker compose up -d

echo ""
echo "=== Deployed ==="
docker compose ps
echo ""
echo "Logs:    docker compose logs -f"
echo "Stop:    docker compose down"
echo "Restart: docker compose restart"
