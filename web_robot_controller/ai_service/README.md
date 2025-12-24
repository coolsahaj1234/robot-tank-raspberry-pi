# AI Video Processing Service

This service processes video frames from the robot camera to provide:
- Lane detection
- Obstacle/wall detection
- Path prediction
- Navigation commands

## Setup

1. Install dependencies:
```bash
cd ai_service
pip install -r requirements.txt
```

2. Start the service:
```bash
python server.py
```

The service will run on `http://localhost:5000`

## API Endpoints

### POST /process_frame
Process a video frame and return AI analysis.

**Request:**
```json
{
  "frame": "base64_encoded_image_string"
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

