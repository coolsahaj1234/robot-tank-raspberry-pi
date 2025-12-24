# Quick Start Guide

## 🚀 Start Everything with One Command

```bash
cd web_robot_controller
npm start
```

That's it! The script will:
- ✅ Check all prerequisites
- ✅ Install missing dependencies
- ✅ Start all services automatically

## What Gets Started

1. **Node.js Bridge Server** (port 3002)
   - WebSocket server for browser
   - TCP client to robot server

2. **React Frontend** (port 5173)
   - Modern UI for robot control
   - Open `http://localhost:5173` in browser

3. **Python AI Service** (port 5001)
   - Video processing for AI mode
   - Lane and obstacle detection

## Alternative: Bash Script

```bash
cd web_robot_controller
./start.sh
```

## Manual Start (if needed)

```bash
# Terminal 1: Bridge Server
npm run server

# Terminal 2: React Client  
npm run client

# Terminal 3: AI Service
cd ai_service
source venv/bin/activate
python3 server.py
```

## Troubleshooting

### Port Already in Use
If a port is already in use, the script will warn you. Stop the conflicting service or change the port in the config.

### Missing Dependencies
The script will automatically install:
- Node.js packages (npm install)
- React packages (client dependencies)
- Python packages (AI service)

### Python Virtual Environment
The script creates `ai_service/venv` automatically. If you need to recreate it:
```bash
cd ai_service
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Services URLs

- **Frontend**: http://localhost:5173
- **Bridge HTTP**: http://localhost:3001
- **Bridge WebSocket**: ws://localhost:3002
- **AI Service**: http://localhost:5001

## Stopping Services

Press `Ctrl+C` in the terminal where you ran `npm start`. All services will stop together.

