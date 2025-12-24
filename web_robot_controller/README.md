# Web Robot Controller

A modern web-based interface to control your robot tank, featuring real-time video streaming, intelligent movement controls, and AI-powered autonomous navigation with radar visualization.

## Quick Start

```bash
cd web_robot_controller
./start.sh
```

This will:
- Check all prerequisites (Node.js, Python, dependencies)
- Install missing dependencies automatically
- Start all services (Bridge server, React frontend, AI service)
- Display service status with logs

**Access the app at:** http://localhost:5173

To stop all services:
```bash
./stop.sh
# Or press Ctrl+C in the terminal running start.sh
```

## Prerequisites

- **Node.js** 16+ and npm
- **Python** 3.8+ and pip3
- **Robot server** running on Raspberry Pi (ports 5003/8003)

## Architecture

```
Browser (React Frontend - port 5173)
    ↓ WebSocket (port 3002)
Node.js Bridge Server
    ↓ TCP
Robot Server (Raspberry Pi - ports 5003/8003)

Browser (React Frontend)
    ↓ HTTP POST (frames + sensor data)
Python AI Service (port 5001)
    ↓ Returns: processed frame, navigation commands, radar data
```

## Features

### Manual Control (Modes 0-3)
- **D-pad**: Click for 100ms pulsed movement
- **Keyboard**: Arrow keys for continuous movement
- **Speed Control**: Adjustable speed slider (10-100%)
- **Servo Control**: Lift and claw servos
- **LED Control**: Color picker and modes
- **Sensor Display**: Real-time distance readings

### AI Autonomous Mode (Mode 4)
- **Reactive Navigation**: Robot never stops - always moves and avoids obstacles
- **Sensor Fusion**: Combines camera vision with ultrasonic sensors
- **Radar Display**: Real-time ultrasonic radar with path tracking
- **Zone Detection**: Visual zones (left/center/right) for smarter avoidance
- **Turn Indicators**: LEDs indicate turning direction
- **Recovery Mode**: Automatically recovers when stuck

**Motor Power Requirements:**
- Forward movement: 55% minimum
- Turns: 70% minimum

### Navigation States
| State | Description | LED Color |
|-------|-------------|-----------|
| Exploring | Normal forward movement | Cyan breathing |
| Avoiding | Obstacle detected, turning | Amber |
| Recovering | Stuck, alternating turns | Red |

## Project Structure

```
web_robot_controller/
├── start.sh              # Start all services
├── stop.sh               # Stop all services
├── package.json          # Node.js dependencies
├── server/               # Node.js bridge server
│   └── index.js         # WebSocket/TCP bridge
├── client/              # React frontend
│   └── src/
│       ├── components/  # UI components (including RadarView)
│       └── hooks/       # Navigation & AI hooks
└── ai_service/          # Python AI processing
    ├── server.py        # Flask API server
    ├── ai_processor.py  # Reactive navigation logic
    └── requirements.txt # Python dependencies
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| React Frontend | 5173 | Web UI |
| Bridge HTTP | 3001 | Status endpoint |
| Bridge WebSocket | 3002 | Real-time communication |
| AI Service | 5001 | Video processing & navigation |

## Usage

1. **Start the robot server** on the Raspberry Pi

2. **Start the controller:**
   ```bash
   ./start.sh
   ```

3. **Open browser:** http://localhost:5173

4. **Connect to robot:**
   - Click "Connect" button
   - Default IP: `10.0.0.86` (change in settings if needed)

5. **Control the robot:**
   - Modes 0-3: Manual control with D-pad/keyboard
   - Mode 4 (AI Auto): Autonomous navigation

## AI Mode Details

The AI mode uses reactive navigation that **never stops** the robot:

1. **Danger Zone** (< 25cm): Immediate turn at 75% power
2. **Caution Zone** (25-50cm): Slow down or turn if needed
3. **Clear Zone** (> 50cm): Normal forward movement at 65%

The radar display shows:
- Ultrasonic distance as colored arc
- Robot heading indicator
- Path history trail
- Detected obstacles

## Troubleshooting

### Services won't start
```bash
# Check prerequisites
node --version    # Should be 16+
python3 --version # Should be 3.8+

# Check ports
lsof -i :3001,3002,5001,5173

# Kill stuck processes
./stop.sh
```

### AI service errors
```bash
# Install dependencies manually
cd ai_service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Robot not moving in AI mode
- Check that robot requires 70% for turns, 55% for forward
- Check AI service logs: `tail -f logs/ai_service.log`
- Verify ultrasonic sensor is working

### Video feed not working
- Verify robot server is running on Pi
- Check network connectivity to robot IP
- Verify ports 5003/8003 are accessible

## Development

```bash
# Install all dependencies
npm run install-all
cd ai_service && pip3 install -r requirements.txt

# Start in development mode (with hot reload)
npm run dev

# Or start services individually:
npm run server     # Bridge server only
npm run client     # React frontend only
npm run ai-service # AI service only
```

## Log Files

When running with `./start.sh`, logs are saved to:
- `logs/bridge.log` - Bridge server logs
- `logs/ai_service.log` - AI service logs
- `logs/frontend.log` - Frontend build logs

## License

MIT
