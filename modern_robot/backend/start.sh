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
echo "   - Installing spidev..."
pip install -q spidev

echo "✅ All dependencies installed."

# Create PID file directory if it doesn't exist
mkdir -p .run

echo "🚀 Starting FastAPI server..."
echo "   Host: 0.0.0.0"
echo "   Port: 8000"
echo "====================================="
echo "Press Ctrl+C to stop the server"

# Permission Fixes for PWM (Optional, but helps if not running as sudo)
# Try to set permissions on PWM chips if they exist
if [ -d "/sys/class/pwm/pwmchip0" ]; then
    echo "🔧 Setting PWM permissions..."
    # Attempt to use sudo if available to fix permissions
    if command -v sudo &> /dev/null; then
        sudo chown -R root:gpio /sys/class/pwm/pwmchip0 || true
        sudo chmod -R g+w /sys/class/pwm/pwmchip0 || true
        # Ensure channels are exported
        if [ ! -d "/sys/class/pwm/pwmchip0/pwm0" ]; then echo 0 | sudo tee /sys/class/pwm/pwmchip0/export > /dev/null || true; fi
        if [ ! -d "/sys/class/pwm/pwmchip0/pwm1" ]; then echo 1 | sudo tee /sys/class/pwm/pwmchip0/export > /dev/null || true; fi
        if [ ! -d "/sys/class/pwm/pwmchip0/pwm3" ]; then echo 3 | sudo tee /sys/class/pwm/pwmchip0/export > /dev/null || true; fi
        # Permission on period/duty_cycle
        sudo chmod 777 /sys/class/pwm/pwmchip0/pwm*/period /sys/class/pwm/pwmchip0/pwm*/duty_cycle /sys/class/pwm/pwmchip0/pwm*/enable 2>/dev/null || true
    fi
fi

# Start the server with sudo to ensure hardware access (PWM, SPI, GPIO)
# We use the python binary from the virtual environment
echo "🔒 Requesting sudo for hardware access..."
sudo ./venv/bin/python3 -m uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 --reload &
SERVER_PID=$!
echo $SERVER_PID > .run/server.pid

# Handle shutdown gracefully
trap 'echo ""; echo "🛑 Shutting down server..."; sudo kill $SERVER_PID 2>/dev/null; rm -f .run/server.pid; echo "Server stopped."; exit 0' INT TERM

# Wait for server process
wait $SERVER_PID
