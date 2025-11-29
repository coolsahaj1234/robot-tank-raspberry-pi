#!/bin/bash

# Robot Backend Startup Script
# This script sets up the virtual environment and starts the FastAPI server

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "====================================="
echo "Robot Backend Server Startup"
echo "====================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Create PID file directory if it doesn't exist
mkdir -p .run

echo "Starting FastAPI server..."
echo "Server will be available at http://0.0.0.0:8000"
echo "Press Ctrl+C to stop the server"
echo "====================================="

# Start the server and save PID
uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 --reload &
SERVER_PID=$!
echo $SERVER_PID > .run/server.pid

# Handle shutdown gracefully
trap 'echo ""; echo "Shutting down server..."; kill $SERVER_PID 2>/dev/null; rm -f .run/server.pid; echo "Server stopped."; exit 0' INT TERM

# Wait for server process
wait $SERVER_PID
