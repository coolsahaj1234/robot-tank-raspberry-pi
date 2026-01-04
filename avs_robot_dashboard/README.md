# AVS Robot Dashboard

This project provides **Situational Awareness and Debugging Interface** for your Raspberry Pi robot tank using Uber's AVS (Autonomous Visualization System) via XVIZ protocol.

## Overview

The AVS Robot Dashboard transforms your robot from a "black box" into a transparent system where you can see exactly what sensors are detecting and what the AI is thinking in real-time.

### Key Features

1. **Live 3D World Reconstruction**
   - Visualize robot pose and orientation relative to surroundings
   - Track robot position and movement over time
   - See robot's "God's eye" view of its environment

2. **Sensor Fusion Visualization**
   - **Ultrasonic Sensors**: Real-time distance cones showing front/back obstacle detection
     - Color-coded: Green (safe) → Orange (caution) → Red (danger)
     - Visual cones represent sensor field of view
   - **Camera Feed**: Live front-facing camera stream integrated into 3D environment
   - **IMU Data**: Acceleration and gyroscope data for pose tracking

3. **AI Vision Debugging (YOLOv8)**
   - Real-time object detection with 3D bounding boxes
   - Visual verification of AI object identification
   - Depth estimation from bounding box analysis
   - Color-coded objects by type (Person, Santa Hat, Furniture, etc.)

4. **Safety & Path Planning**
   - Debug ground visualization for collision avoidance testing
   - Visual detection boxes show where AI thinks objects are in 3D space
   - Test navigation algorithms before full autonomous operation

## Prerequisites

-   Python 3.9+
-   Node.js 14+
-   Robot Server running on `10.0.0.86` (or update `ROBOT_IP` in `backend/main.py`)

## Installation

### Backend Dependencies

```bash
cd backend
pip3 install -r requirements.txt
```

### Frontend Dependencies

```bash
cd frontend
npm install
```

## Running the Dashboard

### Quick Start

Use the provided startup script:

```bash
./start_dashboard.sh
```

This will start both backend and frontend automatically.

### Manual Start

#### 1. Start the Backend (XVIZ Server)
The backend connects to the robot's video stream (port 8003) and command port (port 5003) to receive sensor data, then serves XVIZ data over WebSockets (port 8081).

```bash
cd backend
python3 main.py
```

The backend will:
- Connect to robot video stream for camera frames
- Connect to robot command port for ultrasonic and IMU sensor data
- Run YOLOv8 object detection on each frame
- Build XVIZ visualization data
- Broadcast updates to connected frontend clients

#### 2. Start the Frontend (Streetscape.gl)
The frontend connects to the backend and renders the 3D visualization.

```bash
cd frontend
npm start
```

Open [http://localhost:3000](http://localhost:3000) (or whichever port React opens) to view the dashboard.

## Architecture

-   **Backend** (`backend/main.py`): 
    - Connects to robot's TCP video stream (port 8003)
    - Connects to robot's command port (port 5003) for sensor data
    - Parses `CMD_SONIC` and `CMD_IMU` messages
    - Runs YOLOv8 object detection via `ai_processor.py`
    - Constructs XVIZ snapshots via `xviz_builder.py`
    - Serves XVIZ data over WebSocket (port 8081)

-   **Frontend** (`frontend/src/App.js`): 
    - React application using `streetscape.gl`
    - Connects to backend via WebSocket
    - Renders live 3D visualization with:
      - Robot pose and trajectory
      - Ultrasonic sensor cones
      - Camera feed overlay
      - 3D object detection boxes
      - Debug ground plane

## Configuration

### Robot IP Address

Edit `backend/main.py` to change the robot IP:

```python
ROBOT_IP = '10.0.0.86'  # Change to your robot's IP
```

### Ports

- **Video Port**: 8003 (robot's video stream)
- **Command Port**: 5003 (robot's sensor data)
- **WebSocket Port**: 8081 (XVIZ data to frontend)

## Visualization Details

### Sensor Visualization

- **Front Ultrasonic**: Green/Orange/Red cone pointing forward (+X)
- **Back Ultrasonic**: Blue cone pointing backward (-X)
- **IMU Data**: Used for pose tracking and orientation

### Object Detection

- Objects are mapped from 2D image coordinates to 3D world space
- Depth estimation based on bounding box size
- Lateral position calculated from bounding box center
- Color coding by object type and confidence

### Coordinate System

- **X**: Forward (positive = robot's front)
- **Y**: Left (positive = robot's left side)
- **Z**: Up (positive = upward)

## Troubleshooting

### Backend won't connect to robot

- Verify robot server is running
- Check robot IP address is correct
- Ensure ports 8003 and 5003 are accessible
- Check firewall settings

### No sensor data

- Verify command port connection (check logs for "Connected to Robot Command")
- Ensure robot is sending `CMD_SONIC` and `CMD_IMU` messages
- Check robot server is in manual or ultrasonic mode

### Frontend shows "Connecting to Robot..."

- Verify backend is running on port 8081
- Check browser console for WebSocket connection errors
- Ensure backend logs show "XVIZ Server running"

## Use Cases

1. **Debugging Navigation**: See exactly where obstacles are detected and how the robot responds
2. **AI Verification**: Verify YOLOv8 is correctly identifying objects
3. **Path Planning**: Test collision avoidance algorithms visually
4. **Sensor Calibration**: Visualize sensor readings to verify calibration
5. **Development**: Understand robot behavior during autonomous operation
