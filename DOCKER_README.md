# Robot Tank Docker Deployment Guide

This guide explains how to run the Robot Tank web interfaces using Docker on Windows with limited RAM (4GB).

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Available Services](#available-services)
- [Configuration](#configuration)
- [Memory Optimization](#memory-optimization)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

## Prerequisites

### System Requirements
- **Windows 10/11** with Docker Desktop installed
- **Minimum 4GB RAM** (optimized for low memory usage)
- **Docker Desktop** version 4.0 or higher
- **WSL 2** backend enabled in Docker Desktop

### Install Docker Desktop

1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop/
2. Run the installer
3. Enable WSL 2 backend during installation
4. Restart your computer
5. Open Docker Desktop and ensure it's running

### Configure Docker Desktop for 4GB RAM

1. Open Docker Desktop
2. Go to **Settings** → **Resources**
3. Set **Memory** to **2 GB** (Windows needs 1.5-2GB for OS)
4. Set **CPUs** to **2** (or 3-4 if you have more CPU cores)
5. Set **Swap** to **1 GB** (helps with memory spikes)
6. Click **Apply & Restart**

**Important:** With only 4GB total RAM, you MUST run only ONE service at a time!

## Quick Start

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd robot-tank-raspberry-pi-1
```

### 2. Configure Robot IP Address

Create a `.env` file in the project root:

```bash
# Copy the example
copy .env.example .env

# Edit .env and set your robot's IP address
ROBOT_IP=10.0.0.86
ROBOT_COMMAND_PORT=5003
ROBOT_VIDEO_PORT=8003
```

### 3. Run ONE Service at a Time (REQUIRED for 4GB RAM)

**IMPORTANT:** You MUST run only one service at a time on a 4GB system!

**Option A: Web Robot Controller** (Simple Interface)
```bash
docker-compose up web-robot-controller
```
Access at: http://localhost:8080

**Option B: AVS Robot Dashboard** (Advanced 3D Visualization)
```bash
docker-compose up avs-robot-dashboard
```
Access at: http://localhost:3000

### ⚠️ DO NOT Run Both Services on 4GB RAM
Running both services simultaneously will cause:
- System freezing
- Out of memory errors
- Windows instability
- Docker crashes

**If you have 8GB+ RAM**, you can run both services.

## Available Services

### 1. Web Robot Controller
**Port:** http://localhost:8080
**Memory Usage:** ~1.2-1.8GB
**Features:**
- Simple web interface for robot control
- Real-time video feed
- Manual control with keyboard/gamepad
- AI object detection (YOLOv8)
- Servo and LED control

**Use Case:** Lightweight control interface, ideal for basic operations
**Best for:** 4GB RAM systems, everyday control tasks

### 2. AVS Robot Dashboard
**Port:** http://localhost:3000
**Memory Usage:** ~1.4-2GB
**Features:**
- Advanced 3D visualization using XVIZ
- Real-time pose tracking
- IMU sensor data display (accelerometer + gyroscope)
- AI object detection with 3D positioning
- Autonomous navigation visualization

**Use Case:** Advanced monitoring and autonomous navigation development
**Best for:** 4GB+ RAM systems, development and debugging

## Configuration

### Environment Variables

Edit the `.env` file to configure:

```env
# Robot IP address (find using your router or robot's display)
ROBOT_IP=10.0.0.86

# Robot communication ports
ROBOT_COMMAND_PORT=5003
ROBOT_VIDEO_PORT=8003
```

### Custom Configuration

To modify service behavior, edit `docker-compose.yml`:

```yaml
services:
  web-robot-controller:
    environment:
      - ROBOT_IP=${ROBOT_IP:-10.0.0.86}
      # Add more environment variables here
```

## Memory Optimization

### For 4GB RAM Systems

**Reality Check:**
- Windows OS: ~1.5-2GB (cannot reduce)
- Available for Docker: ~2-2.5GB maximum
- **You can only run ONE service at a time**

**Strategy 1: Run One Service at a Time** (REQUIRED)
```bash
# Start only ONE service
docker-compose up web-robot-controller
# OR
docker-compose up avs-robot-dashboard
```

**Strategy 2: Close Unnecessary Programs** (CRITICAL)
Before starting Docker:
- Close web browsers (especially Chrome - uses lots of RAM)
- Close other Docker containers
- Close heavy applications (Visual Studio, etc.)
- Close background apps you don't need

**Strategy 3: Use Web Robot Controller** (Lighter Option)
If you're tight on RAM:
```bash
# Use the lighter service
docker-compose up web-robot-controller
```

**Strategy 4: Increase Virtual Memory/Swap** (Windows)
1. System Properties → Advanced → Performance Settings
2. Advanced → Virtual Memory → Change
3. Set custom size: Initial 4096MB, Maximum 8192MB
4. Restart computer

### Monitor Memory Usage

```bash
# Check container memory usage
docker stats

# View logs
docker-compose logs -f web-robot-controller
docker-compose logs -f avs-robot-dashboard
```

## Docker Commands

### Basic Operations

```bash
# Start services in foreground (see logs)
docker-compose up

# Start services in background
docker-compose up -d

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild images after code changes
docker-compose build

# Rebuild and start
docker-compose up --build
```

### Individual Service Control

```bash
# Start only web-robot-controller
docker-compose up web-robot-controller

# Start only avs-robot-dashboard
docker-compose up avs-robot-dashboard

# Rebuild specific service
docker-compose build web-robot-controller
```

### Maintenance

```bash
# View logs
docker-compose logs -f

# Enter container shell (for debugging)
docker exec -it web-robot-controller /bin/bash
docker exec -it avs-robot-dashboard /bin/bash

# Remove unused images to free space
docker system prune -a

# Check disk usage
docker system df
```

## Troubleshooting

### Issue: Docker Desktop Won't Start
**Solution:**
1. Enable Virtualization in BIOS
2. Enable WSL 2: `wsl --install` in PowerShell (Admin)
3. Restart computer

### Issue: "Out of Memory" Errors
**Solution:**
1. Run only one service at a time
2. Increase Docker memory in Settings → Resources
3. Close other programs
4. Try: `docker system prune -a` to free space

### Issue: Build Fails with "No Space Left"
**Solution:**
```bash
# Clean up Docker
docker system prune -a --volumes

# Check disk space
docker system df
```

### Issue: Cannot Connect to Robot
**Solution:**
1. Verify robot IP: `ping <ROBOT_IP>`
2. Check `.env` file has correct ROBOT_IP
3. Ensure robot is powered on and connected to network
4. Check firewall settings (allow ports 5003, 8003)

### Issue: Port Already in Use
**Solution:**
```bash
# Find and stop the process using the port
netstat -ano | findstr :8080
taskkill /PID <process_id> /F

# Or change port in docker-compose.yml:
ports:
  - "8090:8080"  # Use port 8090 instead
```

### Issue: Slow Performance
**Solution:**
1. Run one service at a time
2. Reduce CPU usage in Docker Settings
3. Close browser tabs and other programs
4. Use web-robot-controller (lighter than avs-robot-dashboard)

### Issue: Container Keeps Restarting
**Solution:**
```bash
# Check logs for errors
docker-compose logs web-robot-controller

# Common fixes:
# - Check robot is accessible
# - Verify environment variables
# - Ensure ports aren't blocked
```

## Development

### Making Code Changes

1. Edit source code in `web_robot_controller/` or `avs_robot_dashboard/`
2. Rebuild the image:
   ```bash
   docker-compose build web-robot-controller
   ```
3. Restart the container:
   ```bash
   docker-compose up web-robot-controller
   ```

### Using Local Development (No Docker)

If Docker is too heavy for your system, run locally:

**Web Robot Controller:**
```bash
cd web_robot_controller
npm install
cd client && npm install && cd ..
npm start
```

**AVS Robot Dashboard:**
```bash
cd avs_robot_dashboard
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..
# Start backend
cd backend && python main.py &
# Start frontend
cd frontend && npm start
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│           Windows Host (4GB RAM Total)                  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │  Windows OS: ~1.5-2GB (System Reserved)         │ │
│  └──────────────────────────────────────────────────┘ │
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │     Docker Desktop (2-2.5GB allocated)           │ │
│  │                                                  │ │
│  │  ┌─────────────────────────────────────────┐   │ │
│  │  │ web-robot-controller (Option 1)         │   │ │
│  │  │ - Node.js Backend (Express, WS)         │   │ │
│  │  │ - React Frontend (Vite, built)          │   │ │
│  │  │ - Python AI Service (Flask, YOLOv8)     │   │ │
│  │  │ Memory: 1.2-1.8GB                       │   │ │
│  │  │ Ports: 8080 (Web), 5001 (AI)           │   │ │
│  │  └─────────────────────────────────────────┘   │ │
│  │                                                  │ │
│  │               OR (Not Both!)                     │ │
│  │                                                  │ │
│  │  ┌─────────────────────────────────────────┐   │ │
│  │  │ avs-robot-dashboard (Option 2)          │   │ │
│  │  │ - Python Backend (WebSocket, XVIZ)      │   │ │
│  │  │ - React Frontend (CRA, streetscape.gl)  │   │ │
│  │  │ - AI Processing (YOLOv8, OpenCV)        │   │ │
│  │  │ Memory: 1.4-2GB                         │   │ │
│  │  │ Ports: 3000 (Web), 8081 (WebSocket)    │   │ │
│  │  └─────────────────────────────────────────┘   │ │
│  │                                                  │ │
│  └──────────────────────────────────────────────────┘ │
│                                                         │
│  Network: robot-network (Docker bridge)                │
└─────────────────────────────────────────────────────────┘
              │
              │ TCP/IP over WiFi/Ethernet
              ▼
┌─────────────────────────────────────────────────────────┐
│         Raspberry Pi Robot Tank                         │
│         IP: 10.0.0.86 (configured in .env)             │
│         Ports: 5003 (Commands), 8003 (Video Stream)    │
└─────────────────────────────────────────────────────────┘

IMPORTANT: Run ONLY ONE service at a time on 4GB RAM systems!
```

## Performance Tips for 4GB Systems

### Critical Rules
1. ⚠️ **NEVER run both services together** - System will crash
2. ⚠️ **Close Chrome/browsers** before starting - They use 500MB-1GB+
3. ⚠️ **Stop other Docker containers** - Check with `docker ps`

### Recommended Workflow
1. **Choose the right service:**
   - Basic control? → Use `web-robot-controller` (lighter)
   - Advanced debugging? → Use `avs-robot-dashboard` (heavier)

2. **Before starting Docker:**
   - Close web browsers
   - Close Visual Studio/IDEs
   - Close background apps
   - Check Task Manager for memory hogs

3. **Start the service:**
   ```bash
   docker-compose up web-robot-controller
   ```

4. **Monitor memory:**
   ```bash
   docker stats
   ```

5. **If system gets slow:**
   - Stop the service (`Ctrl+C`)
   - Run `docker system prune`
   - Restart Docker Desktop
   - Close more apps

### Alternative: Local Development (No Docker)
If Docker is too heavy, run locally without containers:
- Uses less memory (~500MB vs 1.5GB+)
- Requires manual setup of Node.js and Python
- See "Using Local Development" section

## Support

For issues specific to:
- **Docker setup**: Check [Docker Desktop docs](https://docs.docker.com/desktop/windows/)
- **Robot connection**: Verify network and firewall settings
- **Memory issues**: Run one service at a time, close other apps
- **Build failures**: Run `docker system prune -a` to free space

## License

MIT License - See LICENSE file for details
