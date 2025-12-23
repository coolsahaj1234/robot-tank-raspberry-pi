# macOS Robot Tank Controller

A native macOS SwiftUI application for controlling the robot tank via TCP connection to the Raspberry Pi server.

## Features

- **Real-time Video Feed**: Display live camera feed from robot
- **Motor Control**: 
  - 9-directional pad (forward, backward, left, right, diagonals)
  - Keyboard arrow key support
  - Speed control slider
- **Servo Control**: 
  - Lift arm slider (0-180°)
  - Claw/gripper slider (0-180°)
- **LED Control**: 
  - Color picker
  - Mode selector (static, blink, breathing, rainbow, color wipe)
- **Mode Selection**: Stop, Move, Sonar, Infrared modes
- **Quick Actions**: Clamp up, clamp down, clamp stop
- **Sensor Display**: Ultrasonic distance readings
- **Connection Management**: Connect/disconnect, status indicator

## Requirements

- macOS 12.0 or later
- Xcode 14.0 or later
- Swift 5.9 or later

## Setup

1. Open the project in Xcode:
   ```bash
   open macOS_RobotController/RobotController.xcodeproj
   ```

2. If the Xcode project doesn't exist yet, create it:
   - Open Xcode
   - Create a new macOS App project
   - Choose SwiftUI as the interface
   - Add all the Swift files from the `RobotController` folder

3. Configure the project:
   - Set the deployment target to macOS 12.0
   - Ensure "App Sandbox" is disabled or network access is enabled
   - Add network client capability if needed

4. Build and run the app

## Configuration

On first launch, configure the robot IP address in Settings:
- Default IP: `192.168.1.100`
- Command Port: `5003`
- Video Port: `8003`

Settings are persisted using UserDefaults.

## Usage

1. Click the WiFi icon in the top-left to connect to the robot
2. Use the directional pad or arrow keys to control movement
3. Adjust speed with the speed slider
4. Control servos with the lift and claw sliders
5. Change LED colors and modes using the LED control panel
6. Switch between modes (Stop, Move, Sonar, Infrared)
7. Use quick actions for clamp control

## Protocol

The app communicates with the old_robot server using TCP sockets:
- **Command Port (5003)**: Text-based commands with `#` delimiter and `\n` terminator
- **Video Port (8003)**: Binary stream with 4-byte little-endian length header + JPEG data

### Command Format

- `CMD_MOTOR#left_speed#right_speed\n` - Motor control (-100 to 100)
- `CMD_SERVO#index#angle\n` - Servo control (index: 0/1, angle: 0-180)
- `CMD_LED#mode#r#g#b#index\n` - LED control
- `CMD_MODE#mode\n` - Mode selection (0=stop, 1=move, 2=sonar, 3=infrared)
- `CMD_ACTION#action\n` - Actions (0=clamp stop, 1=clamp up, 2=clamp down)

## Architecture

The app follows MVVM architecture:
- **Models**: Data structures and state management
- **Services**: TCP connection, command sending, video streaming
- **ViewModels**: Business logic and state coordination
- **Views**: SwiftUI user interface components

## Notes

- The server must be running on the Raspberry Pi before connecting
- Video stream requires stable network connection
- Keyboard controls work when the app window is focused
- All settings are automatically saved

