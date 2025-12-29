#!/bin/bash

# Function to kill child processes on exit
cleanup() {
    echo "Shutting down AVS Dashboard..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Trap Ctrl+C (SIGINT) and call cleanup
trap cleanup SIGINT

echo "🚀 Starting AVS Robot Dashboard..."

# 1. Start Backend
echo "📦 Starting Backend (XVIZ Server)..."
cd backend
python3 main.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to initialize
sleep 2

# 2. Start Frontend
echo "💻 Starting Frontend (Streetscape.gl)..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo "✅ All systems go!"
echo "   Backend PID: $BACKEND_PID"
echo "   Frontend PID: $FRONTEND_PID"
echo "   Press Ctrl+C to stop everything."

# Wait indefinitely
wait
