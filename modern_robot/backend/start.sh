#!/bin/bash

# Robot Backend Startup Script
# This script sets up the virtual environment, installs dependencies, and starts the server

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "====================================="
echo "🤖 Robot Backend Server Startup"
echo "====================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment found."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing/Updating dependencies..."
echo "   - Upgrading pip..."
pip install -q --upgrade pip
echo "   - Installing requirements.txt..."
pip install -q -r requirements.txt
echo "   - Installing rpi-hardware-pwm..."
pip install -q rpi-hardware-pwm
echo "   - Installing gpiozero & rpi-lgpio..."
pip install -q gpiozero rpi-lgpio
echo "   - Installing ultralytics (YOLOv8)..."
pip install -q ultralytics

echo "✅ All dependencies installed."

# Create PID file directory if it doesn't exist
mkdir -p .run

echo "🚀 Starting FastAPI server..."
echo "   Host: 0.0.0.0"
echo "   Port: 8000"
echo "====================================="
echo "Press Ctrl+C to stop the server"

# Start the server and save PID
uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 --reload &
SERVER_PID=$!
echo $SERVER_PID > .run/server.pid

# Handle shutdown gracefully
trap 'echo ""; echo "🛑 Shutting down server..."; kill $SERVER_PID 2>/dev/null; rm -f .run/server.pid; echo "Server stopped."; exit 0' INT TERM

# Wait for server process
wait $SERVER_PID
