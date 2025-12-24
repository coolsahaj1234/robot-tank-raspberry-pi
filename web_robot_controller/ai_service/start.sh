#!/bin/bash
# Start AI Service

echo "🤖 Starting AI Video Processing Service..."
echo "📦 Installing dependencies if needed..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start server
echo "🚀 Starting AI service on http://localhost:5001"
python server.py

