# Quick Start Guide

## Prerequisites

1. **Raspberry Pi Server**: Ensure the old_robot server is running on your Raspberry Pi
   - The server should be listening on ports 5003 (commands) and 8003 (video)
   - Default IP is typically `192.168.1.100` (adjust in Settings if different)

2. **macOS Requirements**:
   - macOS 12.0 or later
   - Xcode 14.0 or later (for building)

## Building the App

1. **Create Xcode Project** (see SETUP.md for detailed instructions):
   - Open Xcode → Create New Project → macOS App → SwiftUI
   - Name it `RobotController`
   - Save in the `macOS_RobotController` directory

2. **Add Source Files**:
   - Add all Swift files from the `RobotController` folder to your Xcode project
   - Ensure they're added to the target

3. **Configure Project**:
   - Set deployment target to macOS 12.0+
   - Configure network permissions (disable App Sandbox or add network capabilities)

4. **Build & Run**:
   - Press Cmd+R or click the Run button
   - The app should launch

## First Use

1. **Configure Connection**:
   - Click the gear icon (bottom-left) to open Settings
   - Enter your Raspberry Pi's IP address
   - Verify ports (default: 5003, 8003)
   - Click Save

2. **Connect**:
   - Click the WiFi icon (top-left) to connect
   - Status indicator should turn green when connected
   - Video feed should appear automatically

3. **Control the Robot**:
   - Use the directional pad or arrow keys to move
   - Adjust speed with the slider
   - Control servos with the lift/claw sliders
   - Change LED colors and modes
   - Switch between operation modes

## Controls Reference

### Movement
- **Directional Pad**: Click and hold any direction button
- **Arrow Keys**: Press and hold arrow keys (when window is focused)
- **Speed**: Adjust with the speed slider (0-100%)

### Servos
- **Lift Arm**: Slider (0-180°)
- **Claw**: Slider (0-180°)

### LED
- **Color**: Click color picker to choose color
- **Mode**: Select from dropdown (Index, Color Wipe, Blink, Breathing, Rainbow)

### Modes
- **STOP**: Robot stops all movement
- **MOVE**: Manual control mode
- **SONAR**: Ultrasonic sensor mode
- **INFRARED**: Infrared sensor mode

### Quick Actions
- **Clamp Up**: Raise the clamp
- **Clamp Down**: Lower the clamp
- **Clamp Stop**: Stop clamp movement

## Troubleshooting

### Can't Connect
- Verify robot IP address is correct
- Check that robot server is running
- Ensure both devices are on the same network
- Check firewall settings

### No Video Feed
- Verify video port (default 8003)
- Check network bandwidth/stability
- Try disconnecting and reconnecting

### Controls Not Working
- Ensure robot is in correct mode (MOVE mode for manual control)
- Check connection status indicator
- Verify robot server is responding

### Keyboard Not Working
- Click on the app window to ensure it has focus
- Arrow keys only work when window is active

## Network Configuration

The app uses TCP sockets:
- **Command Port**: 5003 (text-based commands)
- **Video Port**: 8003 (binary video stream)

Make sure these ports are:
- Open on the Raspberry Pi firewall
- Not blocked by your Mac's firewall
- Accessible on your local network

