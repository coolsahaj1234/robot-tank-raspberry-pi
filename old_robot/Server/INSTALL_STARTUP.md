# Robot Tank Server - Startup Installation Guide

This guide explains how to set up the robot tank server to start automatically on boot.

## Quick Start

### Option 1: Manual Start (Testing)

Run the startup script manually:

```bash
cd ~/Server
sudo ./start_robot_server.sh
```

This will:
- Check and start pigpiod daemon
- Verify dependencies
- Start the headless server

### Option 2: Auto-Start on Boot (Recommended)

Set up the systemd service for automatic startup:

```bash
cd ~/Server

# Copy the service file to systemd directory
sudo cp robot-tank-server.service /etc/systemd/system/

# Edit the service file to match your actual paths
sudo nano /etc/systemd/system/robot-tank-server.service
```

**Important:** Update these paths in the service file to match your system:
- `WorkingDirectory=/home/pi5/Server` → Change to your actual Server directory path
- `ExecStart=/bin/bash /home/pi5/Server/start_robot_server.sh` → Change to your actual script path

Then:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable the service (starts on boot)
sudo systemctl enable robot-tank-server.service

# Start the service now
sudo systemctl start robot-tank-server.service

# Check status
sudo systemctl status robot-tank-server.service
```

## Service Management

### Start the service:
```bash
sudo systemctl start robot-tank-server.service
```

### Stop the service:
```bash
sudo systemctl stop robot-tank-server.service
```

### Restart the service:
```bash
sudo systemctl restart robot-tank-server.service
```

### Check status:
```bash
sudo systemctl status robot-tank-server.service
```

### View logs:
```bash
sudo journalctl -u robot-tank-server.service -f
```

### Disable auto-start:
```bash
sudo systemctl disable robot-tank-server.service
```

## Troubleshooting

### Service won't start

1. Check the service status:
   ```bash
   sudo systemctl status robot-tank-server.service
   ```

2. Check the logs:
   ```bash
   sudo journalctl -u robot-tank-server.service -n 50
   ```

3. Verify paths in the service file are correct:
   ```bash
   sudo nano /etc/systemd/system/robot-tank-server.service
   ```

4. Test the startup script manually:
   ```bash
   cd ~/Server
   sudo ./start_robot_server.sh
   ```

### pigpiod not starting

1. Check if pigpiod is installed:
   ```bash
   which pigpiod
   ls -la /usr/local/bin/pigpiod
   ```

2. Start pigpiod manually:
   ```bash
   sudo pigpiod
   ```

3. Check if pigpiod is running:
   ```bash
   ps aux | grep pigpiod
   ```

4. If pigpiod service exists, enable it:
   ```bash
   sudo systemctl enable pigpiod
   sudo systemctl start pigpiod
   ```

### Permission errors

The service runs as root (required for GPIO access). If you see permission errors:

1. Ensure the script is executable:
   ```bash
   chmod +x ~/Server/start_robot_server.sh
   ```

2. Check file ownership:
   ```bash
   ls -la ~/Server/start_robot_server.sh
   ```

## Manual Startup Script Features

The `start_robot_server.sh` script:

- ✅ Checks if pigpiod is running, starts it if not
- ✅ Verifies Python dependencies
- ✅ Checks for required server files
- ✅ Starts the headless server
- ✅ Provides colored output for easy reading
- ✅ Handles errors gracefully

## Files

- `start_robot_server.sh` - Manual startup script
- `robot-tank-server.service` - Systemd service file
- `server_headless.py` - The actual server code

## Notes

- The server requires root/sudo access for GPIO control
- pigpiod should be started before the server for best servo performance
- The service will automatically restart if it crashes (RestartSec=10)
- Logs are available via `journalctl`

