#!/bin/bash

# Telegram Bot Scheduler - Deployment Script
# This script deploys the bot to a server with Docker installed

set -e

echo "==================================="
echo "Telegram Bot Scheduler Deployment"
echo "==================================="
echo ""

# Function to install Docker on Ubuntu/Debian
install_docker_ubuntu() {
    echo "Installing Docker on Ubuntu/Debian..."
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    echo "Docker installed successfully!"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed on this server."
    echo ""
    read -p "Would you like to install Docker now? (y/n): " install_choice
    
    if [[ $install_choice =~ ^[Yy]$ ]]; then
        install_docker_ubuntu
        
        echo ""
        echo "IMPORTANT: You need to log out and log back in for Docker group membership to take effect."
        echo "After logging back in, run this script again."
        exit 0
    else
        echo "Docker installation cancelled. Please install Docker manually: https://docs.docker.com/engine/install/"
        exit 1
    fi
fi

# Check if Docker Compose is installed
if ! docker compose version &> /dev/null; then
    echo "Docker Compose plugin is not installed."
    echo ""
    echo "This should have been installed with Docker."
    echo "Please reinstall Docker or install the compose plugin manually."
    exit 1
fi

# Prompt for environment variables if .env doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    echo ""
    
    read -p "Enter your Telegram Bot Token: " BOT_TOKEN
    read -p "Enter your Groq API Key: " GROQ_KEY
    
    cat > .env << EOF
TELEGRAM_BOT_TOKEN=${BOT_TOKEN}
GROQ_API_KEY=${GROQ_KEY}
EOF
    
    echo ".env file created successfully!"
    echo ""
fi

# Create schedules.db if it doesn't exist
if [ ! -f schedules.db ]; then
    echo "Creating empty schedules.db file..."
    touch schedules.db
    echo "schedules.db created successfully!"
    echo ""
fi

# Stop existing container if running
echo "Stopping existing containers..."
docker compose down 2>/dev/null || true
echo ""

# Build the Docker image
echo "Building Docker image..."
docker compose build
echo ""

# Start the container
echo "Starting the bot..."
docker compose up -d
echo ""

# Show status
echo "==================================="
echo "Deployment completed successfully!"
echo "==================================="
echo ""
echo "Bot status:"
docker compose ps
echo ""
echo "To view logs: docker compose logs -f"
echo "To stop bot: docker compose down"
echo "To restart bot: docker compose restart"
echo ""
