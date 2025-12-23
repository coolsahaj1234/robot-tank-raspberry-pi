# Server Setup Guide

## The Problem

You have **two different server systems**:

1. **old_robot/Server** - Uses raw TCP sockets (ports 5003/8003)
   - Works with: macOS app I created, or old Python client
   - Protocol: Raw TCP with text commands

2. **modern_robot/backend** - Uses HTTP/WebSocket (port 8000)
   - Works with: React frontend (`modern_robot/frontend`)
   - Protocol: Socket.IO + HTTP REST API

## Solution: Choose One Server

### Option A: Use Modern Robot Backend (For React Frontend)

**On your Raspberry Pi**, run:

```bash
cd ~/robot-tank-raspberry-pi/modern_robot/backend
./start.sh
```

This will:
- Start the server on port **8000**
- Support Socket.IO/WebSocket connections
- Work with your React frontend

**On your Mac**, configure the frontend:
1. Open http://localhost:5173
2. Click the gear icon (Settings)
3. Enter your Pi's IP: `10.0.0.86`
4. Port: `8000` (default)
5. Click Save & Connect

### Option B: Use Old Robot Server (For macOS App)

**On your Raspberry Pi**, keep running:
```bash
cd ~/Server
python3 server_headless.py
```

**On your Mac**, use the macOS app I created (requires Xcode setup).

## Current Situation

Your Pi is running the **old_robot server** (TCP on 5003/8003), but your frontend is trying to connect to the **modern_robot backend** (WebSocket on 8000).

**To fix immediately:**
1. Stop the old server on Pi (Ctrl+C)
2. Start the modern_robot backend instead
3. Your frontend will connect automatically

## Port Reference

| Server Type | Command Port | Video Port | Protocol |
|------------|--------------|------------|----------|
| old_robot | 5003 | 8003 | Raw TCP |
| modern_robot | 8000 | 8000 | HTTP/WebSocket |

## Quick Fix Command

**On Raspberry Pi:**
```bash
# Stop old server (if running)
pkill -f server_headless.py

# Start modern robot backend
cd ~/robot-tank-raspberry-pi/modern_robot/backend
./start.sh
```

**On Mac:**
- Frontend should auto-connect to `10.0.0.86:8000`
- Or set it manually in Settings

