# AVS Robot Dashboard

This project visualizes the Raspberry Pi Robot's state using Uber's AVS (Autonomous Visualization System) via XVIZ protocol.

## Prerequisites

-   Python 3.9+
-   Node.js 14+
-   Robot Server running on `10.0.0.86` (or update `backend/main.py`)

## Running the Dashboard

### 1. Start the Backend (XVIZ Server)
The backend connects to the robot and serves XVIZ data over WebSockets (port 8081).

```bash
cd backend
python3 main.py
```

### 2. Start the Frontend (Streetscape.gl)
The frontend connects to the backend and renders the 3D visualization.

```bash
cd frontend
npm start
```

Open [http://localhost:3000](http://localhost:3000) (or whichever port React opens) to view the dashboard.

## Architecture

-   **Backend**: Python. Connects to the robot's raw TCP video stream, runs YOLOv8/OpenCV object detection, and constructs XVIZ snapshots.
-   **Frontend**: React + `streetscape.gl`. Connects to the backend via WebSocket to receive live XVIZ data.
