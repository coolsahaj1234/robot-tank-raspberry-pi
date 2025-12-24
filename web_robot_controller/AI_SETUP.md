# AI Autonomous Navigation Setup

This guide will help you set up the AI-powered autonomous navigation system for your robot tank.

## Architecture

```
React Frontend (Browser)
    ↓ HTTP POST
Python AI Service (localhost:5001)
    ↓ Processes frames
    ↓ Returns navigation commands
React Frontend
    ↓ Executes commands
Node.js Bridge Server
    ↓ TCP
Robot Server (Raspberry Pi)
```

## Features

- **Lane Detection**: Uses OpenCV to detect lane lines in the camera feed
- **Obstacle Detection**: Detects walls and obstacles in the robot's path
- **Path Prediction**: Predicts the robot's path forward (Tesla-style visualization)
- **Autonomous Navigation**: Automatically controls motors and LEDs based on AI analysis
- **Turn Indicators**: Uses LED lights to indicate turning direction (2 LEDs on each side)

## Setup Instructions

### 1. Install Python Dependencies

```bash
cd web_robot_controller/ai_service
pip install -r requirements.txt
```

Or use the startup script:
```bash
cd web_robot_controller/ai_service
./start.sh
```

### 2. Start All Services

From the `web_robot_controller` directory:

```bash
npm run dev
```

This will start:
- Node.js bridge server (port 3002)
- React frontend (port 5173)
- Python AI service (port 5001)

### 3. Using AI Mode

1. Connect to your robot (click "Connect" button)
2. Select "AI Auto" mode from the bottom panel
3. The UI will switch to dual-camera view:
   - **Left**: Live camera feed
   - **Right**: AI-processed feed with overlays

## How It Works

### Lane Detection
- Uses Canny edge detection and Hough transform
- Detects left and right lane lines
- Calculates center offset to keep robot centered
- Shows predicted path as a yellow curve

### Obstacle Detection
- Analyzes contours in the forward path
- Detects walls and obstacles
- Automatically slows down when obstacles are detected
- Plans turns to avoid obstacles

### Navigation Commands
The AI service generates commands:
- **Speed**: Adjusted based on obstacles (slows down near walls)
- **Turn Direction**: Left or right based on lane/obstacle position
- **LED Control**: Flashes left or right LEDs to indicate turning

### LED Turn Indicators
- **Left Turn**: LEDs 0 and 1 (left side) flash amber/yellow
- **Right Turn**: LEDs 2 and 3 (right side) flash amber/yellow
- **Straight**: All LEDs off

## API Endpoints

### POST /process_frame
Process a video frame and get AI analysis.

**Request:**
```json
{
  "frame": "base64_encoded_image"
}
```

**Response:**
```json
{
  "processed_frame": "base64_encoded_processed_image",
  "lane_data": {
    "left_lane": [...],
    "right_lane": [...],
    "center_offset": 0.0,
    "turn_direction": "left" | "right" | null
  },
  "obstacle_data": {
    "obstacles": [...],
    "nearest_obstacle": {...},
    "obstacle_distance": 50.0,
    "should_turn": false,
    "turn_direction": "left" | "right" | null
  },
  "navigation_command": {
    "speed": 50,
    "turn": "left" | "right" | null,
    "led_left": false,
    "led_right": false
  }
}
```

## Troubleshooting

### AI Service Not Starting
- Check Python version: `python3 --version` (needs 3.7+)
- Install dependencies: `pip install -r requirements.txt`
- Check port 5001 is available

### No Processed Frames
- Check browser console for errors
- Verify AI service is running: `curl http://localhost:5001/health`
- Check network tab for failed requests

### Robot Not Moving in AI Mode
- Ensure robot is connected
- Check that "AI Auto" mode is selected
- Verify navigation commands are being generated (check console logs)

## Customization

You can modify the AI behavior in `ai_service/ai_processor.py`:
- Adjust lane detection sensitivity
- Change obstacle detection thresholds
- Modify speed reduction when obstacles detected
- Customize LED colors/patterns

