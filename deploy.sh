#!/bin/bash

# Exit on error
set -e

echo "====================================="
echo "   Deploying VPN Sub Proxy (Docker)  "
echo "====================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "[!] Docker is not installed. Please install Docker first:"
    echo "    sudo apt update && sudo apt install docker.io docker-compose -y"
    exit 1
fi

# Ensure .env exists
if [ ! -f .env ]; then
    echo "[!] Error: .env file not found."
    echo "    Please create a .env file with TARGET_SERVER_URL, PROXY_PASSWORD, and SECRET_KEY."
    exit 1
fi

echo "[+] Building and starting Docker container in the background..."
# Try modern docker compose plugin first, fallback to docker-compose binary
if docker compose version &> /dev/null; then
    docker compose up -d --build
else
    docker-compose up -d --build
fi

echo "[+] Deployment successful!"
echo "    The proxy is now running on port 5000."
echo "    To view live logs, run: docker logs -f vpn-sub-proxy"
