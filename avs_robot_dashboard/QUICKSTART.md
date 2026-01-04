# AVS Robot Dashboard - Quick Start Guide

## First Time Setup

```bash
# 1. Navigate to project directory
cd /Users/sandeepsingh/Documents/robot-tank-raspberry-pi-1/avs_robot_dashboard

# 2. Install all dependencies (Python packages, npm packages, Depth Pro, YOLO models)
./dashboard.sh install
```

This will install:
- Backend Python packages (OpenCV, ultralytics, websockets, torch, etc.)
- Apple Depth Pro (for accurate depth estimation)
- YOLO models (YOLOv11m or YOLOv8x for better object detection)
- Frontend npm packages (React, streetscape.gl, etc.)

## Daily Usage

### Start Everything
```bash
./dashboard.sh start
```
This starts both backend (port 8081) and frontend (port 3000).
Access the dashboard at: http://localhost:3000

### Stop Everything
```bash
./dashboard.sh stop
```

### Restart After Code Changes
```bash
# Restart everything
./dashboard.sh restart

# Or restart only what you changed
./dashboard.sh restart-backend   # After editing backend code
./dashboard.sh restart-frontend  # After editing frontend code
```

### Check Status
```bash
./dashboard.sh status
```

Shows if backend and frontend are running, their PIDs, and ports.

## Viewing Logs

```bash
# View all logs (last 50 lines)
./dashboard.sh logs

# View backend logs only
./dashboard.sh logs backend

# View frontend logs only
./dashboard.sh logs frontend

# View more lines
./dashboard.sh logs backend 100

# Follow logs in real-time
./dashboard.sh follow
./dashboard.sh follow backend
```

## Production Build

```bash
# Build optimized frontend for production
./dashboard.sh build
```

## Troubleshooting

### Backend won't start
```bash
# Check backend logs
./dashboard.sh logs backend

# Common issues:
# - Port 8081 already in use: ./dashboard.sh stop-backend
# - Missing dependencies: ./dashboard.sh install
# - Robot not connected: Check robot IP in backend/main.py
```

### Frontend won't start
```bash
# Check frontend logs
./dashboard.sh logs frontend

# Common issues:
# - Port 3000 already in use: ./dashboard.sh stop-frontend
# - Missing node_modules: cd frontend && npm install
```

### Depth Pro not working
```bash
# Reinstall Depth Pro
pip3 install --upgrade depth-pro

# Check logs for "Using fallback" message
./dashboard.sh logs backend | grep -i depth

# System will work with fallback estimation if Depth Pro fails
```

### YOLO detection poor
The script installs better models automatically, but you can verify:
```bash
python3 -c "from ultralytics import YOLO; print(YOLO('yolo11m.pt'))"
```

## All Available Commands

```
./dashboard.sh install           # Install all dependencies
./dashboard.sh start             # Start everything
./dashboard.sh stop              # Stop everything
./dashboard.sh restart           # Restart everything
./dashboard.sh status            # Show status
./dashboard.sh logs [service]    # View logs
./dashboard.sh follow [service]  # Follow logs in real-time
./dashboard.sh build             # Build frontend for production
./dashboard.sh clean             # Clean log files
./dashboard.sh help              # Show help
```

## File Locations

```
Dashboard Script:    ./dashboard.sh
Backend Logs:        ./logs/backend.log
Frontend Logs:       ./logs/frontend.log
Backend Code:        ./backend/
Frontend Code:       ./frontend/
Depth Pro Setup:     ./backend/DEPTH_PRO_SETUP.md
```

## Quick Tips

1. **Always use the script**: `./dashboard.sh` handles PIDs, ports, and logs automatically
2. **Check logs first**: When something breaks, `./dashboard.sh logs` usually shows why
3. **Status is your friend**: `./dashboard.sh status` shows what's running
4. **GPU recommended**: Depth Pro works much faster with GPU (MPS on Mac, CUDA on Linux)

## Next Steps

After starting the dashboard:

1. **Check object detection**: Look at the camera feed and AVS 3D map
2. **Verify depth**: Objects should appear at correct distances in 3D map
3. **Monitor performance**: Check logs for frame rates and depth estimation times
4. **Tune as needed**: See `backend/DEPTH_PRO_SETUP.md` for configuration options

---

**Need Help?**
- Check logs: `./dashboard.sh logs`
- Full setup guide: `backend/DEPTH_PRO_SETUP.md`
- Script help: `./dashboard.sh help`
