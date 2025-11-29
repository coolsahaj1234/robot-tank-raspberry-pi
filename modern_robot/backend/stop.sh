#!/bin/bash

# Robot Backend Shutdown Script
# This script gracefully stops the running FastAPI server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "====================================="
echo "Robot Backend Server Shutdown"
echo "====================================="

PID_FILE=".run/server.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")

    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping server (PID: $PID)..."
        kill $PID

        # Wait for process to terminate
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done

        # Force kill if still running
        if ps -p $PID > /dev/null 2>&1; then
            echo "Force stopping server..."
            kill -9 $PID
        fi

        rm -f "$PID_FILE"
        echo "Server stopped successfully."
    else
        echo "Server process not found (PID: $PID)"
        rm -f "$PID_FILE"
    fi
else
    echo "No running server found (PID file not found)"

    # Try to find and kill any uvicorn process
    UVICORN_PID=$(pgrep -f "uvicorn app.main:socket_app")
    if [ ! -z "$UVICORN_PID" ]; then
        echo "Found uvicorn process (PID: $UVICORN_PID), stopping..."
        kill $UVICORN_PID
        echo "Server stopped."
    else
        echo "No uvicorn process running."
    fi
fi

echo "====================================="
