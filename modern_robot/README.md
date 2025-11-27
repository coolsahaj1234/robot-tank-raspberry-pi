# Modern Modular Robot System

This project is a complete, modern rewrite of the Freenove Raspberry Pi Tank Kit software. It features a responsive web-based command center, a modular Python backend with FastAPI, and AI capabilities using YOLOv8.

## 🚀 Features

### Architecture
- **Backend**: Python (FastAPI + Socket.IO) running on Raspberry Pi 5.
- **Frontend**: React (Vite + Tailwind CSS) running on any client device.
- **Communication**: Low-latency WebSockets for control; MJPEG streaming for video.

### Capabilities
- **Dual Camera System**: 
  - Front Camera (Fixed behind arm)
  - Rear Camera (Mounted on 180° servo for panoramic view)
- **3-Degree-of-Freedom Arm**: Control for Lift, Clamp/Claw, and Rear Camera Pan.
- **Autonomy Levels**:
  - **Manual**: Full user control via Joystick/UI.
  - **Semi-Auto**: (Placeholder) AI assisted suggestions.
  - **Full-Auto**: (Placeholder) Autonomous navigation (safety overrides enabled).
- **AI Processing**:
  - Integrated YOLOv8 for object detection (Person, Trash, etc.) running on the Pi.
  - "Mock Mode" for testing UI/Logic on non-Pi hardware.
- **Responsive UI**:
  - Mobile-friendly dashboard.
  - Configurable IP address to connect to the robot from any device on the network.

## 🛠 Hardware Requirements

- **Raspberry Pi 5 (8GB recommended)**
- **Freenove Tank Kit Chassis & Motors**
- **Servos**:
  - Port 12: Arm Lift
  - Port 13: Claw/Pinch
  - Port 19: Rear Camera Pan (New addition)
- **Cameras**:
  - 2x USB or CSI Cameras (Mapped to indices 0 and 1)

## 📦 Installation

### 1. Backend (Raspberry Pi)

Prerequisites: Python 3.9+, system dependencies for OpenCV/GPIO.

```bash
cd modern_robot/backend

# Install dependencies
pip install -r requirements.txt

# Install YOLOv8 (Ultralytics) and PyTorch
pip install ultralytics torch torchvision
```

**Hardware Access**: Ensure your user has access to GPIO and Video groups.
```bash
sudo usermod -a -G gpio,video $USER
```

### 2. Frontend (Client)

Prerequisites: Node.js 18+

```bash
cd modern_robot/frontend

# Install dependencies
npm install
```

## 🎮 Usage

### Starting the Server
On the Raspberry Pi:
```bash
cd modern_robot/backend
python3 -m uvicorn app.main:socket_app --host 0.0.0.0 --port 8000
```
*Note: If `gpiozero` is not found, the system defaults to "MOCK MODE" (simulated hardware).*

### Starting the Client
On your Laptop/PC:
```bash
cd modern_robot/frontend
npm run dev
```
Open your browser to `http://localhost:5173`.

### Connecting Remotely
1. Click the **Settings (Gear)** icon in the sidebar.
2. Enter the IP address of your Raspberry Pi (e.g., `192.168.1.50`).
3. Click **Save & Connect**.

## 🧠 AI Features
The backend automatically loads a lightweight YOLOv8 Nano model (`yolov8n.pt`).
- **Mock Mode**: Generates random noise frames with bounding boxes.
- **Real Mode**: Performs inference on live camera feeds.

## 📂 Directory Structure

```
modern_robot/
├── backend/
│   ├── app/
│   │   ├── core/           # Robot logic, Hardware drivers (HAL)
│   │   ├── services/       # AI services (YOLO)
│   │   └── api/            # REST & WebSocket endpoints
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/     # Dashboard, Joystick, Video Panels
    │   └── lib/            # Socket.io connection logic
    └── package.json
```
