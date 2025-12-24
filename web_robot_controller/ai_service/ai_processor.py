#!/usr/bin/env python3
"""
AI Video Processing Service - Reactive Navigation
Uses reactive obstacle avoidance with potential fields for robust navigation.
Optimized for 2 ultrasonic sensors + front camera setup.
"""

import cv2
import numpy as np
import base64
import json
import time
from typing import Dict, Tuple, Optional, List, Any
from collections import deque
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def to_json_serializable(obj: Any) -> Any:
    """Convert numpy types to JSON-serializable Python types"""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {k: to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [to_json_serializable(item) for item in obj]
    elif isinstance(obj, deque):
        return [to_json_serializable(item) for item in obj]
    return obj


class AIVideoProcessor:
    """
    Deliberate Navigation AI Processor

    Philosophy: STOP, ANALYZE, then MOVE in chunks
    - Not reactive/continuous - deliberate and careful
    - Stops to analyze when obstacles detected
    - Moves in timed chunks, then stops to reassess
    """

    def __init__(self):
        # AI thinking log - stores last N thoughts
        self.thinking_log = deque(maxlen=15)
        self.log_counter = 0
        # Navigation state machine
        # States: 'analyzing', 'moving_forward', 'turning_left', 'turning_right', 'stopped'
        self.navigation_state = 'analyzing'
        self.previous_state = None
        self.state_start_time = time.time()

        # Movement chunk timing (in seconds)
        self.MOVE_CHUNK_DURATION = 0.8    # Move forward for 0.8 seconds
        self.TURN_CHUNK_DURATION = 1.0    # Turn for 1.0 second (longer for effective turn)
        self.BACKUP_DURATION = 0.8        # Backup for 0.8 seconds
        self.ANALYZE_DURATION = 0.6       # Analyze for 0.6 seconds before deciding

        # Turn tracking
        self.last_turn_direction = 'right'
        self.escape_direction = 'right'
        self.consecutive_turns = 0
        self.backup_count = 0  # Track how many times we've backed up

        # Frame processing
        self.previous_frame = None
        self.frame_count = 0
        self.frames_in_state = 0

        # Stuck detection - VISUAL based
        self.movement_history = deque(maxlen=10)
        self.stuck_counter = 0
        self.stuck_threshold = 1.5       # If frame diff < this, consider stuck
        self.stuck_frames_needed = 5     # Need 5 consecutive stuck frames
        self.is_currently_stuck = False
        self.last_action = 'stop'        # Track what robot should be doing

        # Speed control - CAREFUL speeds with STRONG turns
        self.forward_speed = 45       # SLOWER forward (was 55)
        self.slow_forward_speed = 35  # Very slow when caution
        self.turn_speed = 90          # STRONG turn speed (was 75) - needs power!
        self.backup_speed = 50        # Backup speed

        # Ultrasonic history for noise filtering (front and back)
        self.ultrasonic_history = deque(maxlen=5)
        self.ultrasonic_back_history = deque(maxlen=5)
        self.back_distance = 100  # Track back distance

        # Movement tracking for radar visualization
        self.position = {'x': 0, 'y': 0, 'heading': 0}
        self.path_history = deque(maxlen=100)
        self.obstacle_map = []

        # Distance thresholds (cm) - MORE CONSERVATIVE
        self.TOO_CLOSE_DISTANCE = 15   # WAY too close - must backup
        self.DANGER_DISTANCE = 30      # Danger - stop and turn/backup
        self.CAUTION_DISTANCE = 50     # Slow down
        self.SAFE_DISTANCE = 80        # Safe to move forward

        # Lane keeping
        self.previous_lanes = None
        self.lane_history = deque(maxlen=10)

        # Object detection settings
        self.min_object_area = 500  # Minimum contour area to consider
        self.detected_objects = []  # Store detected objects for overlay

        logger.info("🤖 Deliberate Navigation AI initialized")

    def log_thought(self, category: str, message: str, level: str = 'info'):
        """Add a thought to the AI thinking log"""
        self.log_counter += 1
        entry = {
            'id': self.log_counter,
            'timestamp': time.time(),
            'category': category,
            'message': message,
            'level': level  # 'info', 'warning', 'danger', 'action'
        }
        self.thinking_log.append(entry)

    def generate_narration(self, nav_command: Dict, detected_objects: List[Dict],
                          front_distance: float, back_distance: float) -> str:
        """
        Generate natural language narration of what the robot is doing.
        Makes the AI feel like a conversational companion with personality.
        """
        import random
        action = nav_command.get('action', 'stop')
        is_stuck = nav_command.get('is_stuck', False)
        left_clear = nav_command.get('left_clear', True)
        right_clear = nav_command.get('right_clear', True)

        # Build object awareness
        close_objects = [o for o in detected_objects if o['distance'] == 'close']
        medium_objects = [o for o in detected_objects if o['distance'] == 'medium']

        # Variety phrases for different situations
        forward_phrases = [
            "All clear ahead! Let's explore.",
            "Path looks good, moving forward.",
            "Nice and clear, rolling along.",
            f"Got {int(front_distance)}cm ahead - plenty of room!"
        ]

        slow_phrases = [
            f"Something ahead at {int(front_distance)}cm. Taking it easy.",
            "Getting closer to something... slowing down.",
            "Approaching carefully to get a better look.",
            "Caution zone - easing forward."
        ]

        backup_phrases = [
            "Whoa, too close! Backing up.",
            "Need some breathing room here.",
            "Reversing to get a better angle.",
            "Backing out of this tight spot."
        ]

        stuck_phrases = [
            "Hmm, I don't seem to be moving. Let me try backing up.",
            "Stuck! Time to try a different approach.",
            "Something's blocking me. Reversing course.",
            "Can't make progress here. Backing up to reassess."
        ]

        turn_left_phrases = [
            "Turning left - looks clearer that way.",
            "Going left to find a better path.",
            "Obstacle on my right, heading left.",
            "Left turn! Let's see what's over there."
        ]

        turn_right_phrases = [
            "Turning right - more room that way.",
            "Right side looks promising.",
            "Avoiding obstacle, going right.",
            "Taking a right here, looks better."
        ]

        analyze_phrases = [
            "Let me check out my surroundings...",
            "Scanning the area...",
            "Planning my next move...",
            "Assessing the situation..."
        ]

        stop_phrases = [
            "Holding position, thinking...",
            "Stopping to evaluate options.",
            "Pausing to figure out the best route.",
            "Taking a moment to plan ahead."
        ]

        # Select narration based on action
        if is_stuck:
            narration = random.choice(stuck_phrases)
        elif action == 'forward':
            narration = random.choice(forward_phrases)
        elif action == 'slow_forward':
            narration = random.choice(slow_phrases)
        elif action == 'backup':
            narration = random.choice(backup_phrases)
        elif action == 'turn_left':
            narration = random.choice(turn_left_phrases)
        elif action == 'turn_right':
            narration = random.choice(turn_right_phrases)
        elif action == 'analyzing':
            narration = random.choice(analyze_phrases)
        elif action == 'stop':
            narration = random.choice(stop_phrases)
        else:
            narration = "Exploring..."

        # Add object awareness if detected
        if close_objects:
            obj_names = [o['type'].lower() for o in close_objects[:2]]
            if len(obj_names) == 1:
                narration += f" I see a {obj_names[0]} nearby."
            else:
                narration += f" There's a {obj_names[0]} and {obj_names[1]} in view."

        # Add contextual warnings
        if front_distance < 15 and action != 'backup':
            narration += " Very close to something!"
        elif not left_clear and not right_clear and action not in ['backup', 'turn_left', 'turn_right']:
            narration += " Both sides look tight."

        return narration

    def get_thinking_log(self) -> list:
        """Get the current thinking log as a list"""
        return list(self.thinking_log)

    def detect_objects(self, image: np.ndarray) -> List[Dict]:
        """
        Detect and classify objects in the image using contour analysis.
        Returns list of detected objects with bounding boxes and classifications.
        """
        height, width = image.shape[:2]
        detected = []

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Use adaptive thresholding for better edge detection
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )

        # Find edges using Canny
        edges = cv2.Canny(blurred, 50, 150)

        # Combine threshold and edges
        combined = cv2.bitwise_or(thresh, edges)

        # Dilate to connect nearby edges
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(combined, kernel, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_object_area:
                continue

            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)

            # Skip if too small or too large (probably noise or background)
            if w < 30 or h < 30 or w > width * 0.9 or h > height * 0.9:
                continue

            # Calculate aspect ratio and other properties
            aspect_ratio = float(w) / h
            extent = area / (w * h)  # How much of bounding box is filled
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            solidity = area / hull_area if hull_area > 0 else 0

            # Approximate contour to polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            vertices = len(approx)

            # Calculate center position
            cx = x + w // 2
            cy = y + h // 2

            # Determine position in frame (left, center, right)
            if cx < width // 3:
                position = 'left'
            elif cx > 2 * width // 3:
                position = 'right'
            else:
                position = 'center'

            # Classify object based on properties
            obj_type, confidence, color = self._classify_object(
                area, aspect_ratio, extent, solidity, vertices, w, h, cy, height
            )

            # Calculate distance estimate based on size and position
            # Objects lower in frame are closer
            vertical_pos = cy / height  # 0 = top, 1 = bottom
            size_factor = (w * h) / (width * height)
            distance_estimate = 'far'
            if vertical_pos > 0.6 or size_factor > 0.1:
                distance_estimate = 'close'
            elif vertical_pos > 0.4 or size_factor > 0.05:
                distance_estimate = 'medium'

            detected.append({
                'type': obj_type,
                'confidence': confidence,
                'bbox': [x, y, w, h],
                'center': [cx, cy],
                'position': position,
                'distance': distance_estimate,
                'area': area,
                'color': color
            })

        # Sort by area (largest first) and limit to top 5
        detected.sort(key=lambda x: x['area'], reverse=True)
        self.detected_objects = detected[:5]

        return self.detected_objects

    def _classify_object(self, area, aspect_ratio, extent, solidity,
                         vertices, w, h, cy, img_height) -> Tuple[str, float, Tuple[int, int, int]]:
        """
        Classify detected object based on shape properties.
        Returns (type_name, confidence, color_bgr)
        """
        # Wall/Large obstacle - very wide, spans most of width
        if aspect_ratio > 2.5 and extent > 0.5:
            return ('WALL', 0.8, (0, 0, 255))  # Red

        # Box/Furniture - roughly square, high solidity
        if 0.7 < aspect_ratio < 1.4 and solidity > 0.8 and extent > 0.6:
            return ('BOX', 0.75, (255, 128, 0))  # Orange

        # Tall object (person, pole, furniture)
        if aspect_ratio < 0.6 and h > w * 1.5:
            if solidity > 0.6:
                return ('PERSON', 0.6, (255, 0, 255))  # Magenta
            else:
                return ('POLE', 0.65, (128, 128, 255))  # Light blue

        # Round object (ball, wheel)
        if vertices > 6 and 0.7 < aspect_ratio < 1.3 and solidity > 0.75:
            return ('ROUND', 0.7, (0, 255, 255))  # Yellow

        # Wide obstacle (table, bench)
        if aspect_ratio > 1.5 and solidity > 0.5:
            return ('WIDE OBJ', 0.65, (0, 165, 255))  # Orange

        # Small object
        if area < 2000:
            return ('SMALL', 0.5, (128, 255, 128))  # Light green

        # Generic obstacle
        return ('OBSTACLE', 0.6, (0, 200, 200))  # Cyan

    def base64_to_image(self, base64_string: str) -> np.ndarray:
        """Convert base64 string to OpenCV image"""
        try:
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            image_data = base64.b64decode(base64_string)
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            logger.error(f"Error decoding base64 image: {e}")
            return None

    def enhance_low_light(self, image: np.ndarray) -> np.ndarray:
        """Enhance image for low-light conditions using CLAHE"""
        if image is None:
            return None
        try:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l_enhanced = clahe.apply(l)
            lab_enhanced = cv2.merge([l_enhanced, a, b])
            enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

            # Gamma correction for very dark images
            gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
            if np.mean(gray) < 50:
                gamma = 1.5
                table = np.array([((i / 255.0) ** (1.0 / gamma)) * 255
                                  for i in range(256)]).astype("uint8")
                enhanced = cv2.LUT(enhanced, table)
            return enhanced
        except:
            return image

    def get_filtered_ultrasonic(self, distance: float) -> float:
        """Filter front ultrasonic readings to reduce noise using median filter"""
        if distance is None or distance <= 0:
            return 100.0  # Default to safe distance
        self.ultrasonic_history.append(distance)
        if len(self.ultrasonic_history) >= 3:
            return float(np.median(list(self.ultrasonic_history)))
        return distance

    def get_filtered_back_ultrasonic(self, distance: float) -> float:
        """Filter back ultrasonic readings"""
        if distance is None or distance <= 0:
            return 100.0
        self.ultrasonic_back_history.append(distance)
        if len(self.ultrasonic_back_history) >= 3:
            return float(np.median(list(self.ultrasonic_back_history)))
        return distance

    def detect_movement(self, current_frame: np.ndarray) -> float:
        """
        Detect if the image is changing using simple frame difference.
        Returns the amount of change between frames.
        """
        if current_frame is None:
            return 10.0  # Assume moving

        if self.previous_frame is None:
            self.previous_frame = current_frame.copy()
            return 10.0  # First frame, assume moving

        try:
            # Resize for faster processing
            small_current = cv2.resize(current_frame, (160, 120))
            small_previous = cv2.resize(self.previous_frame, (160, 120))

            # Convert to grayscale
            gray_current = cv2.cvtColor(small_current, cv2.COLOR_BGR2GRAY)
            gray_previous = cv2.cvtColor(small_previous, cv2.COLOR_BGR2GRAY)

            # Calculate absolute difference
            diff = cv2.absdiff(gray_current, gray_previous)

            # Calculate mean difference (how much the image changed)
            mean_diff = float(np.mean(diff))

            # Store in history
            self.movement_history.append(mean_diff)
            self.previous_frame = current_frame.copy()

            return mean_diff
        except Exception as e:
            logger.debug(f"Movement detection error: {e}")
            self.previous_frame = current_frame.copy() if current_frame is not None else None
            return 5.0

    def check_if_stuck(self, current_action: str) -> bool:
        """
        Check if robot is stuck based on visual feedback.
        If robot should be moving but image isn't changing → STUCK
        """
        # Only check for stuck when robot SHOULD be moving
        moving_actions = ['forward', 'slow_forward', 'turn_left', 'turn_right']

        if current_action not in moving_actions:
            # Not supposed to be moving, reset stuck counter
            self.stuck_counter = 0
            self.is_currently_stuck = False
            return False

        if len(self.movement_history) < 3:
            return False

        # Get recent frame differences
        recent = list(self.movement_history)[-5:]
        avg_movement = np.mean(recent)

        # If image isn't changing much while we should be moving → stuck!
        if avg_movement < self.stuck_threshold:
            self.stuck_counter += 1
            if self.stuck_counter >= self.stuck_frames_needed:
                if not self.is_currently_stuck:
                    logger.warning(f"🚨 STUCK DETECTED! Frame diff={avg_movement:.2f} while action={current_action}")
                self.is_currently_stuck = True
                return True
        else:
            # Image is changing, not stuck
            self.stuck_counter = max(0, self.stuck_counter - 2)
            if self.stuck_counter == 0:
                self.is_currently_stuck = False

        return self.is_currently_stuck

    def update_position(self, speed: float, turn: str, dt: float = 0.1):
        """Update estimated position for movement tracking visualization"""
        # Simple dead reckoning for visualization
        heading_change = 0
        if turn == 'left':
            heading_change = -15  # degrees
        elif turn == 'right':
            heading_change = 15

        self.position['heading'] = (self.position['heading'] + heading_change) % 360

        # Update position based on heading and speed
        heading_rad = np.radians(self.position['heading'])
        distance = speed * dt * 0.5  # Scale factor for visualization

        self.position['x'] += distance * np.sin(heading_rad)
        self.position['y'] += distance * np.cos(heading_rad)

        # Add to path history
        self.path_history.append({
            'x': self.position['x'],
            'y': self.position['y'],
            'heading': self.position['heading'],
            'timestamp': time.time()
        })

    def add_obstacle_to_map(self, distance: float, angle_offset: float = 0):
        """Add detected obstacle to the map for radar visualization"""
        if distance is None or distance <= 0 or distance > 200:
            return

        # Calculate obstacle position relative to robot
        heading_rad = np.radians(self.position['heading'] + angle_offset)
        obs_x = self.position['x'] + distance * np.sin(heading_rad)
        obs_y = self.position['y'] + distance * np.cos(heading_rad)

        self.obstacle_map.append({
            'x': obs_x,
            'y': obs_y,
            'distance': distance,
            'timestamp': time.time()
        })

        # Keep only recent obstacles (last 50)
        if len(self.obstacle_map) > 50:
            self.obstacle_map = self.obstacle_map[-50:]
    
    def image_to_base64(self, image: np.ndarray) -> str:
        """Convert OpenCV image to base64 string"""
        try:
            _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 80])
            return base64.b64encode(buffer).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image to base64: {e}")
            return None

    def detect_lanes(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], Dict]:
        """Detect lanes using edge detection and Hough transform"""
        if image is None:
            return None, {}

        enhanced = self.enhance_low_light(image)
        gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Adaptive edge detection
        mean_brightness = np.mean(blurred)
        low_thresh = 30 if mean_brightness < 60 else 50
        high_thresh = 100 if mean_brightness < 60 else 150
        edges = cv2.Canny(blurred, low_thresh, high_thresh)

        height, width = edges.shape

        # ROI - lower 60% trapezoid
        roi_vertices = np.array([[
            (0, height),
            (width * 0.3, height * 0.4),
            (width * 0.7, height * 0.4),
            (width, height)
        ]], dtype=np.int32)

        mask = np.zeros_like(edges)
        cv2.fillPoly(mask, roi_vertices, 255)
        masked_edges = cv2.bitwise_and(edges, mask)

        lines = cv2.HoughLinesP(masked_edges, 1, np.pi/180, 40, minLineLength=40, maxLineGap=80)

        overlay = image.copy()
        lane_data = {'left_lane': None, 'right_lane': None, 'center_offset': 0, 'turn_direction': None}

        if lines is not None:
            left_lines, right_lines = [], []

            for line in lines:
                x1, y1, x2, y2 = line[0]
                if x2 - x1 == 0:
                    continue
                slope = (y2 - y1) / (x2 - x1)

                if abs(slope) > 0.3:
                    if slope < 0:
                        left_lines.append(line[0])
                    else:
                        right_lines.append(line[0])

            # Draw lanes
            for ll in left_lines:
                cv2.line(overlay, (ll[0], ll[1]), (ll[2], ll[3]), (0, 255, 0), 2)
            for rl in right_lines:
                cv2.line(overlay, (rl[0], rl[1]), (rl[2], rl[3]), (0, 255, 0), 2)

            lane_data['left_lane'] = left_lines
            lane_data['right_lane'] = right_lines

            # Calculate offset
            if left_lines and right_lines:
                left_x = np.mean([l[0] + l[2] for l in left_lines]) / 2
                right_x = np.mean([l[0] + l[2] for l in right_lines]) / 2
                lane_center = (left_x + right_x) / 2
                offset = lane_center - (width / 2)
                lane_data['center_offset'] = float(offset)

                if abs(offset) > 25:
                    lane_data['turn_direction'] = 'left' if offset < 0 else 'right'

        # Draw center reference
        cv2.line(overlay, (width // 2, height), (width // 2, int(height * 0.4)), (255, 0, 0), 1)

        return overlay, lane_data
    
    def detect_obstacles(self, image: np.ndarray, ultrasonic_distance: float = None) -> Tuple[Optional[np.ndarray], Dict]:
        """
        Detect obstacles using visual analysis + ultrasonic sensor fusion.
        Optimized for reactive navigation.
        """
        if image is None:
            return None, {}

        # Filter ultrasonic reading
        filtered_distance = self.get_filtered_ultrasonic(ultrasonic_distance)

        overlay = image.copy()
        height, width = image.shape[:2]
        center_x = width // 2

        obstacle_data = {
            'obstacles': [],
            'nearest_obstacle': None,
            'obstacle_distance': filtered_distance,
            'ultrasonic_distance': filtered_distance,
            'should_turn': False,
            'turn_direction': None,
            'danger_zone': 'clear',  # 'clear', 'caution', 'danger'
            'left_clear': True,
            'right_clear': True,
            'center_blocked': False
        }

        # Enhance and process image
        enhanced = self.enhance_low_light(image)
        gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Edge detection with adaptive thresholds
        mean_brightness = np.mean(blurred)
        low_thresh = 30 if mean_brightness < 60 else 50
        high_thresh = 100 if mean_brightness < 60 else 150
        edges = cv2.Canny(blurred, low_thresh, high_thresh)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Divide image into 3 zones: left, center, right
        left_zone = width // 3
        right_zone = 2 * width // 3
        forward_region_y = height // 2

        obstacles_in_path = []
        left_obstacles = 0
        center_obstacles = 0
        right_obstacles = 0

        min_area = max(200, (height * width) / 15000)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(contour)
                center_contour_x = x + w // 2

                # Only consider obstacles in forward half of image
                if y < forward_region_y + height // 4:
                    confidence = min(1.0, area / (height * width * 0.08))

                    obstacle = {
                        'x': int(x), 'y': int(y),
                        'width': int(w), 'height': int(h),
                        'center_x': int(center_contour_x),
                        'area': float(area),
                        'confidence': float(confidence),
                        'zone': 'center'
                    }

                    # Determine zone
                    if center_contour_x < left_zone:
                        obstacle['zone'] = 'left'
                        left_obstacles += 1
                    elif center_contour_x > right_zone:
                        obstacle['zone'] = 'right'
                        right_obstacles += 1
                    else:
                        obstacle['zone'] = 'center'
                        center_obstacles += 1

                    obstacles_in_path.append(obstacle)

                    # Draw with zone-based colors
                    color = (0, 255, 0) if obstacle['zone'] == 'center' else (255, 165, 0)
                    if confidence > 0.5:
                        color = (0, 0, 255)
                    cv2.rectangle(overlay, (x, y), (x + w, y + h), color, 2)

        obstacle_data['obstacles'] = obstacles_in_path
        obstacle_data['left_clear'] = left_obstacles < 2
        obstacle_data['right_clear'] = right_obstacles < 2
        obstacle_data['center_blocked'] = center_obstacles > 1

        # Determine danger zone based on ultrasonic distance
        if filtered_distance < self.DANGER_DISTANCE:
            obstacle_data['danger_zone'] = 'danger'
            obstacle_data['should_stop'] = True
            # Add to obstacle map for radar
            self.add_obstacle_to_map(filtered_distance, 0)
        elif filtered_distance < self.CAUTION_DISTANCE:
            obstacle_data['danger_zone'] = 'caution'
            obstacle_data['should_stop'] = True
        else:
            obstacle_data['danger_zone'] = 'clear'
            obstacle_data['should_stop'] = False

        # Determine preferred turn direction based on which side is clearer
        if obstacle_data['left_clear'] and not obstacle_data['right_clear']:
            obstacle_data['turn_direction'] = 'left'
        elif obstacle_data['right_clear'] and not obstacle_data['left_clear']:
            obstacle_data['turn_direction'] = 'right'
        elif obstacles_in_path:
            # Turn away from nearest obstacle
            nearest = min(obstacles_in_path, key=lambda o: o['y'])
            obstacle_data['nearest_obstacle'] = nearest
            obstacle_data['turn_direction'] = 'right' if nearest['center_x'] < center_x else 'left'
        else:
            # Default - alternate turns
            obstacle_data['turn_direction'] = self.last_turn_direction

        # Draw danger zone indicator
        zone_color = {'clear': (0, 255, 0), 'caution': (0, 165, 255), 'danger': (0, 0, 255)}
        cv2.rectangle(overlay, (10, 10), (60, 40), zone_color[obstacle_data['danger_zone']], -1)
        cv2.putText(overlay, f"{int(filtered_distance)}cm", (15, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Draw zone divisions
        cv2.line(overlay, (left_zone, 0), (left_zone, height), (100, 100, 100), 1)
        cv2.line(overlay, (right_zone, 0), (right_zone, height), (100, 100, 100), 1)

        return overlay, obstacle_data

    def _detect_obstacles_simple(self, image: np.ndarray, front_distance: float) -> Dict:
        """
        Simplified obstacle detection - uses ultrasonic as primary, camera for side detection.
        Does NOT draw on the image (keeps it clean).
        """
        if image is None:
            return {'left_clear': True, 'right_clear': True, 'center_blocked': False, 'danger_zone': 'clear'}

        height, width = image.shape[:2]

        # Convert to grayscale and detect edges
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        # Divide into zones
        left_zone = edges[:, :width//3]
        center_zone = edges[:, width//3:2*width//3]
        right_zone = edges[:, 2*width//3:]

        # Count edge pixels in each zone (more edges = more obstacles)
        left_density = np.sum(left_zone) / left_zone.size
        center_density = np.sum(center_zone) / center_zone.size
        right_density = np.sum(right_zone) / right_zone.size

        threshold = 15  # Adjust based on environment

        obstacle_data = {
            'left_clear': left_density < threshold,
            'right_clear': right_density < threshold,
            'center_blocked': center_density > threshold,
            'danger_zone': 'clear',
            'left_density': float(left_density),
            'right_density': float(right_density),
            'center_density': float(center_density)
        }

        # Set danger zone based on ultrasonic distance
        if front_distance < self.TOO_CLOSE_DISTANCE:
            obstacle_data['danger_zone'] = 'danger'
        elif front_distance < self.DANGER_DISTANCE:
            obstacle_data['danger_zone'] = 'danger'
        elif front_distance < self.CAUTION_DISTANCE:
            obstacle_data['danger_zone'] = 'caution'
        else:
            obstacle_data['danger_zone'] = 'clear'

        return obstacle_data

    def _draw_clean_overlay(self, image: np.ndarray, nav_command: Dict,
                           front_distance: float, back_distance: float) -> np.ndarray:
        """
        Draw a CLEAN, simple overlay on the image.
        Shows only essential info: distances, state, direction.
        """
        if image is None:
            return image

        overlay = image.copy()
        height, width = image.shape[:2]

        action = nav_command.get('action', 'stop')
        state = nav_command.get('state', 'analyzing')

        # Colors
        GREEN = (0, 255, 0)
        YELLOW = (0, 255, 255)
        RED = (0, 0, 255)
        CYAN = (255, 255, 0)
        WHITE = (255, 255, 255)

        # Determine status color based on action
        if action == 'backup':
            status_color = RED
            status_text = "BACKING UP"
        elif action in ['turn_left', 'turn_right']:
            status_color = YELLOW
            status_text = f"TURNING {'LEFT' if action == 'turn_left' else 'RIGHT'}"
        elif action == 'forward':
            status_color = GREEN
            status_text = "FORWARD"
        elif action == 'slow_forward':
            status_color = CYAN
            status_text = "SLOW"
        elif action == 'analyzing':
            status_color = CYAN
            status_text = "ANALYZING"
        else:
            status_color = WHITE
            status_text = "STOPPED"

        # --- FRONT DISTANCE BAR (top) ---
        bar_height = 25
        bar_width = width - 20
        bar_x = 10
        bar_y = 10

        # Background
        cv2.rectangle(overlay, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (40, 40, 40), -1)

        # Distance fill (green to red based on distance)
        fill_ratio = min(1.0, front_distance / 100.0)
        fill_width = int(bar_width * fill_ratio)

        if front_distance < self.DANGER_DISTANCE:
            fill_color = RED
        elif front_distance < self.CAUTION_DISTANCE:
            fill_color = YELLOW
        else:
            fill_color = GREEN

        cv2.rectangle(overlay, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height), fill_color, -1)

        # Front distance text
        cv2.putText(overlay, f"FRONT: {int(front_distance)}cm", (bar_x + 5, bar_y + 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1)

        # --- BACK DISTANCE BAR (bottom) ---
        back_bar_y = height - bar_height - 10

        cv2.rectangle(overlay, (bar_x, back_bar_y), (bar_x + bar_width, back_bar_y + bar_height), (40, 40, 40), -1)

        back_fill_ratio = min(1.0, back_distance / 100.0)
        back_fill_width = int(bar_width * back_fill_ratio)

        if back_distance < 20:
            back_fill_color = RED
        elif back_distance < 40:
            back_fill_color = YELLOW
        else:
            back_fill_color = GREEN

        cv2.rectangle(overlay, (bar_x, back_bar_y), (bar_x + back_fill_width, back_bar_y + bar_height), back_fill_color, -1)

        cv2.putText(overlay, f"BACK: {int(back_distance)}cm", (bar_x + 5, back_bar_y + 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1)

        # --- STATUS TEXT (center top) ---
        text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        text_x = (width - text_size[0]) // 2
        text_y = bar_y + bar_height + 30

        # Background for text
        cv2.rectangle(overlay, (text_x - 10, text_y - 25), (text_x + text_size[0] + 10, text_y + 5), (0, 0, 0), -1)
        cv2.putText(overlay, status_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)

        # --- DIRECTION ARROW ---
        arrow_center_x = width // 2
        arrow_center_y = height // 2

        if action == 'turn_left':
            # Left arrow
            pts = np.array([[arrow_center_x - 60, arrow_center_y],
                           [arrow_center_x - 20, arrow_center_y - 30],
                           [arrow_center_x - 20, arrow_center_y + 30]], np.int32)
            cv2.fillPoly(overlay, [pts], YELLOW)
        elif action == 'turn_right':
            # Right arrow
            pts = np.array([[arrow_center_x + 60, arrow_center_y],
                           [arrow_center_x + 20, arrow_center_y - 30],
                           [arrow_center_x + 20, arrow_center_y + 30]], np.int32)
            cv2.fillPoly(overlay, [pts], YELLOW)
        elif action == 'forward' or action == 'slow_forward':
            # Up arrow
            pts = np.array([[arrow_center_x, arrow_center_y - 50],
                           [arrow_center_x - 30, arrow_center_y],
                           [arrow_center_x + 30, arrow_center_y]], np.int32)
            cv2.fillPoly(overlay, [pts], GREEN if action == 'forward' else CYAN)
        elif action == 'backup':
            # Down arrow (backup)
            pts = np.array([[arrow_center_x, arrow_center_y + 50],
                           [arrow_center_x - 30, arrow_center_y],
                           [arrow_center_x + 30, arrow_center_y]], np.int32)
            cv2.fillPoly(overlay, [pts], RED)

        # --- DETECTED OBJECTS ---
        for obj in self.detected_objects:
            x, y, w, h = obj['bbox']
            color = obj['color']
            obj_type = obj['type']
            distance = obj['distance']
            confidence = obj['confidence']

            # Draw bounding box
            thickness = 3 if distance == 'close' else 2
            cv2.rectangle(overlay, (x, y), (x + w, y + h), color, thickness)

            # Draw corner accents for better visibility
            corner_len = min(15, w // 4, h // 4)
            # Top-left corner
            cv2.line(overlay, (x, y), (x + corner_len, y), color, thickness + 1)
            cv2.line(overlay, (x, y), (x, y + corner_len), color, thickness + 1)
            # Top-right corner
            cv2.line(overlay, (x + w, y), (x + w - corner_len, y), color, thickness + 1)
            cv2.line(overlay, (x + w, y), (x + w, y + corner_len), color, thickness + 1)
            # Bottom-left corner
            cv2.line(overlay, (x, y + h), (x + corner_len, y + h), color, thickness + 1)
            cv2.line(overlay, (x, y + h), (x, y + h - corner_len), color, thickness + 1)
            # Bottom-right corner
            cv2.line(overlay, (x + w, y + h), (x + w - corner_len, y + h), color, thickness + 1)
            cv2.line(overlay, (x + w, y + h), (x + w, y + h - corner_len), color, thickness + 1)

            # Label background
            label = f"{obj_type}"
            dist_label = f"[{distance.upper()}]"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]

            # Draw label above the box
            label_y = max(y - 5, 20)
            cv2.rectangle(overlay, (x, label_y - 18), (x + label_size[0] + 60, label_y + 4), (0, 0, 0), -1)
            cv2.putText(overlay, label, (x + 2, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            cv2.putText(overlay, dist_label, (x + label_size[0] + 8, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, WHITE, 1)

        # Blend overlay (semi-transparent)
        result = cv2.addWeighted(image, 0.6, overlay, 0.4, 0)

        return result

    def draw_path_gridlines(self, image: np.ndarray, turn_direction: str = None) -> np.ndarray:
        """
        Draw perspective gridlines showing the path forward.
        Creates a visual guide for the robot's forward path.
        """
        if image is None:
            return image

        overlay = image.copy()
        height, width = image.shape[:2]

        # Define the path corridor - narrows toward the horizon
        horizon_y = int(height * 0.35)  # Horizon line
        bottom_y = height

        # Path width at bottom and top
        path_width_bottom = width * 0.7
        path_width_top = width * 0.15

        # Calculate path boundaries
        center_x = width // 2

        # Shift path if turning
        turn_offset = 0
        if turn_direction == 'left':
            turn_offset = -width * 0.1
        elif turn_direction == 'right':
            turn_offset = width * 0.1

        # Bottom corners
        left_bottom = int(center_x - path_width_bottom / 2 + turn_offset)
        right_bottom = int(center_x + path_width_bottom / 2 + turn_offset)

        # Top corners (horizon)
        left_top = int(center_x - path_width_top / 2 + turn_offset * 0.3)
        right_top = int(center_x + path_width_top / 2 + turn_offset * 0.3)

        # Draw perspective path lines (green corridor)
        line_color = (0, 255, 100)  # Bright green
        line_thickness = 2

        # Left edge of path
        cv2.line(overlay, (left_bottom, bottom_y), (left_top, horizon_y), line_color, line_thickness)
        # Right edge of path
        cv2.line(overlay, (right_bottom, bottom_y), (right_top, horizon_y), line_color, line_thickness)

        # Draw horizontal grid lines at different depths
        num_horizontal_lines = 6
        for i in range(1, num_horizontal_lines):
            # Interpolate y position (closer lines are more spread out due to perspective)
            t = (i / num_horizontal_lines) ** 1.5  # Exponential for perspective
            y = int(bottom_y - t * (bottom_y - horizon_y))

            # Interpolate x positions
            left_x = int(left_bottom + t * (left_top - left_bottom))
            right_x = int(right_bottom + t * (right_top - right_bottom))

            # Draw horizontal line
            cv2.line(overlay, (left_x, y), (right_x, y), line_color, 1)

        # Draw center line (dashed)
        center_top = int(center_x + turn_offset * 0.3)
        dash_length = 15
        gap_length = 10
        y = bottom_y
        while y > horizon_y:
            # Calculate x at this y level
            t = (bottom_y - y) / (bottom_y - horizon_y)
            x = int(center_x + t * turn_offset * 0.3)
            y_end = max(horizon_y, y - dash_length)
            t_end = (bottom_y - y_end) / (bottom_y - horizon_y)
            x_end = int(center_x + t_end * turn_offset * 0.3)

            cv2.line(overlay, (x, y), (x_end, y_end), (255, 255, 0), 2)  # Yellow center line
            y -= (dash_length + gap_length)

        # Draw horizon line
        cv2.line(overlay, (0, horizon_y), (width, horizon_y), (100, 100, 255), 1)

        # Draw direction arrow if turning
        if turn_direction:
            arrow_y = int(height * 0.7)
            arrow_x = center_x
            arrow_length = 50

            if turn_direction == 'left':
                arrow_end = (arrow_x - arrow_length, arrow_y - 20)
                arrow_color = (255, 165, 0)  # Orange
            else:
                arrow_end = (arrow_x + arrow_length, arrow_y - 20)
                arrow_color = (255, 165, 0)

            cv2.arrowedLine(overlay, (arrow_x, arrow_y), arrow_end, arrow_color, 3, tipLength=0.3)

        # Blend overlay with original (semi-transparent gridlines)
        result = cv2.addWeighted(image, 0.7, overlay, 0.3, 0)

        return result

    def process_frame(self, base64_frame: str, ultrasonic_distance: float = None,
                      ultrasonic_distance_back: float = None, scan_direction: str = None) -> Dict:
        """
        Process a single video frame with deliberate navigation.
        Uses both front and back ultrasonic sensors.
        """
        self.frame_count += 1

        # Filter both ultrasonic distances
        front_distance = self.get_filtered_ultrasonic(ultrasonic_distance)
        back_distance = self.get_filtered_back_ultrasonic(ultrasonic_distance_back)
        self.back_distance = back_distance

        # Decode image
        image = self.base64_to_image(base64_frame)
        if image is None:
            return self._generate_default_response(ultrasonic_distance, back_distance)

        # Detect frame change (for stuck detection)
        frame_change = self.detect_movement(image)

        # Process obstacle detection (simplified - no lane detection clutter)
        obstacle_data = self._detect_obstacles_simple(image, front_distance)

        # Detect and classify objects in the frame
        detected_objects = self.detect_objects(image)

        # Log detected objects if any close ones found
        close_objects = [o for o in detected_objects if o['distance'] == 'close']
        if close_objects and self.frame_count % 5 == 0:  # Log every 5th frame to reduce spam
            obj_summary = ', '.join([f"{o['type']}({o['position']})" for o in close_objects[:3]])
            self.log_thought('DETECT', f'Close objects: {obj_summary}', 'warning')

        # Generate navigation command
        nav_command = self._generate_deliberate_command({}, obstacle_data, front_distance, frame_change)

        # Create CLEAN overlay with object detection (not cluttered)
        clean_overlay = self._draw_clean_overlay(image, nav_command, front_distance, back_distance)

        # Update position tracking for radar
        self.update_position(nav_command['speed'], nav_command.get('turn'), 0.1)

        # Convert to base64
        processed_base64 = self.image_to_base64(clean_overlay)

        # Generate natural language narration
        narration = self.generate_narration(nav_command, detected_objects, front_distance, back_distance)

        # Build response with both front and back distances
        response = {
            'processed_frame': processed_base64,
            'obstacle_data': obstacle_data,
            'detected_objects': detected_objects,
            'navigation_command': nav_command,
            'navigation_state': self.navigation_state,
            'frame_change': float(frame_change),
            'narration': narration,
            # Radar/tracking data with BOTH sensors
            'radar_data': {
                'position': self.position.copy(),
                'path_history': list(self.path_history)[-20:],
                'obstacle_map': self.obstacle_map[-10:],
                'ultrasonic_distance': front_distance,
                'ultrasonic_distance_back': back_distance,
                'heading': self.position['heading']
            },
            # AI thinking log for UI
            'thinking_log': self.get_thinking_log()
        }

        return to_json_serializable(response)

    def _generate_default_response(self, ultrasonic_distance: float = None,
                                     ultrasonic_distance_back: float = None) -> Dict:
        """Generate default response when no image available"""
        response = {
            'processed_frame': None,
            'lane_data': {},
            'obstacle_data': {},
            'is_stuck': False,
            'navigation_command': {
                'speed': 0,
                'turn': None,
                'action': 'stop',
                'led_ai_mode': True,
                'led_left': False,
                'led_right': False
            },
            'navigation_state': 'analyzing',
            'radar_data': {
                'position': self.position.copy(),
                'path_history': [],
                'obstacle_map': [],
                'ultrasonic_distance': ultrasonic_distance or 100,
                'ultrasonic_distance_back': ultrasonic_distance_back or 100,
                'heading': 0
            }
        }
        return to_json_serializable(response)

    def _generate_deliberate_command(
        self,
        lane_data: Dict,
        obstacle_data: Dict,
        ultrasonic_distance: float,
        frame_change: float = 10.0
    ) -> Dict:
        """
        Generate DELIBERATE navigation command with SENSOR FUSION and STUCK DETECTION.

        Key behaviors:
        - BACKUP when too close OR all sides blocked OR STUCK
        - STRONG turns (90% power) to actually move
        - SLOW forward movement for safety
        - Commit to actions - don't interrupt mid-turn or mid-backup
        - If image not changing while moving → STUCK → BACKUP
        """
        filtered_distance = self.get_filtered_ultrasonic(ultrasonic_distance)
        current_time = time.time()
        time_in_state = current_time - self.state_start_time
        self.frames_in_state += 1

        # Sensor fusion - get side clearance from visual detection
        left_clear = obstacle_data.get('left_clear', True)
        right_clear = obstacle_data.get('right_clear', True)
        center_blocked = obstacle_data.get('center_blocked', False)

        # Check if stuck (image not changing while should be moving)
        is_stuck = self.check_if_stuck(self.last_action)

        command = {
            'speed': 0,
            'turn': None,
            'action': 'stop',
            'led_ai_mode': True,
            'led_left': False,
            'led_right': False,
            'state': self.navigation_state,
            'distance': filtered_distance,
            'time_in_state': time_in_state,
            'left_clear': left_clear,
            'right_clear': right_clear,
            'frame_change': frame_change,
            'is_stuck': is_stuck
        }

        # ============================================================
        # STUCK DETECTION - Highest priority!
        # If robot is stuck (image not changing while moving), BACKUP!
        # ============================================================
        if is_stuck and self.navigation_state not in ['backing_up', 'analyzing', 'stopped']:
            self.log_thought('STUCK', f'Frame diff={frame_change:.1f} - not moving! Backing up', 'danger')
            logger.warning(f"🚨 STUCK! Image not changing (diff={frame_change:.2f}) - BACKING UP!")
            self._change_state('backing_up')
            self.stuck_counter = 0  # Reset for next detection
            command['speed'] = self.backup_speed
            command['action'] = 'backup'
            command['is_stuck'] = True
            self.last_action = 'backup'
            return command

        # ============================================================
        # STATE MACHINE with BACKUP and SENSOR FUSION
        # ============================================================

        # STATE: BACKING UP - committed, don't interrupt
        if self.navigation_state == 'backing_up':
            command['speed'] = self.backup_speed
            command['action'] = 'backup'
            command['turn'] = None
            self.last_action = 'backup'

            if time_in_state >= self.BACKUP_DURATION:
                self.log_thought('BACKUP', 'Backup complete, finding clear path', 'action')
                logger.info(f"⬅️ Backup complete - now turning")
                self.backup_count += 1
                self.is_currently_stuck = False  # Reset stuck flag
                # After backup, turn to find clear path
                if left_clear and not right_clear:
                    self.log_thought('DECIDE', 'Left clear, right blocked → Turn LEFT', 'info')
                    self._change_state('turning_left')
                elif right_clear:
                    self.log_thought('DECIDE', 'Right clear → Turn RIGHT', 'info')
                    self._change_state('turning_right')
                else:
                    # Still blocked - alternate turn direction
                    new_dir = 'turning_left' if self.last_turn_direction == 'right' else 'turning_right'
                    self.log_thought('DECIDE', f'Both blocked, alternating → {new_dir}', 'warning')
                    self._change_state(new_dir)

            return command  # Don't interrupt backup!

        # STATE: TURNING LEFT - committed, strong power
        if self.navigation_state == 'turning_left':
            command['speed'] = self.turn_speed  # 90% power!
            command['turn'] = 'left'
            command['action'] = 'turn_left'
            command['led_left'] = True
            self.last_turn_direction = 'left'
            self.last_action = 'turn_left'

            if time_in_state >= self.TURN_CHUNK_DURATION:
                logger.info(f"↩️ Left turn complete ({self.TURN_CHUNK_DURATION}s)")
                self._change_state('analyzing')
                self.consecutive_turns += 1

            return command  # Don't interrupt turn!

        # STATE: TURNING RIGHT - committed, strong power
        if self.navigation_state == 'turning_right':
            command['speed'] = self.turn_speed  # 90% power!
            command['turn'] = 'right'
            command['action'] = 'turn_right'
            command['led_right'] = True
            self.last_turn_direction = 'right'
            self.last_action = 'turn_right'

            if time_in_state >= self.TURN_CHUNK_DURATION:
                logger.info(f"↪️ Right turn complete ({self.TURN_CHUNK_DURATION}s)")
                self._change_state('analyzing')
                self.consecutive_turns += 1

            return command  # Don't interrupt turn!

        # ============================================================
        # DANGER CHECKS (only when not in committed action)
        # ============================================================

        # TOO CLOSE - Must backup!
        if filtered_distance < self.TOO_CLOSE_DISTANCE:
            self.log_thought('DANGER', f'TOO CLOSE! {filtered_distance:.0f}cm < {self.TOO_CLOSE_DISTANCE}cm', 'danger')
            logger.warning(f"🚨 TOO CLOSE! {filtered_distance:.0f}cm - BACKING UP!")
            self._change_state('backing_up')
            command['speed'] = self.backup_speed
            command['action'] = 'backup'
            return command

        # DANGER ZONE - Need to stop and decide
        if filtered_distance < self.DANGER_DISTANCE:
            # Check if we have ANY clear direction
            if not left_clear and not right_clear:
                # ALL BLOCKED - Must backup!
                self.log_thought('BLOCKED', f'All sides blocked at {filtered_distance:.0f}cm → BACKUP', 'danger')
                logger.warning(f"🚨 ALL BLOCKED at {filtered_distance:.0f}cm - BACKING UP!")
                self._change_state('backing_up')
                command['speed'] = self.backup_speed
                command['action'] = 'backup'
                return command

            # Have a clear side - stop and turn
            if self.navigation_state != 'stopped':
                self.log_thought('OBSTACLE', f'Obstacle at {filtered_distance:.0f}cm - stopping', 'warning')
                logger.warning(f"🛑 DANGER at {filtered_distance:.0f}cm - stopping to turn")
                self._change_state('stopped')

            command['speed'] = 0
            command['action'] = 'stop'
            command['led_left'] = True
            command['led_right'] = True

            # After brief stop, turn to clear side
            if time_in_state > 0.3:
                if left_clear and not right_clear:
                    self.log_thought('TURN', 'Right blocked → Turning LEFT', 'action')
                    logger.info(f"↩️ Turning LEFT (right blocked)")
                    self._change_state('turning_left')
                elif right_clear and not left_clear:
                    self.log_thought('TURN', 'Left blocked → Turning RIGHT', 'action')
                    logger.info(f"↪️ Turning RIGHT (left blocked)")
                    self._change_state('turning_right')
                else:
                    # Both clear - pick one (alternate)
                    new_dir = 'turning_left' if self.last_turn_direction == 'right' else 'turning_right'
                    self.log_thought('TURN', f'Both clear, alternating → {new_dir.split("_")[1].upper()}', 'action')
                    logger.info(f"🔄 Turning {new_dir.split('_')[1].upper()} (alternating)")
                    self._change_state(new_dir)
            return command

        # ============================================================
        # NORMAL STATES
        # ============================================================

        # STATE: ANALYZING
        if self.navigation_state == 'analyzing':
            command['speed'] = 0
            command['action'] = 'analyzing'
            self.last_action = 'analyzing'

            if time_in_state >= self.ANALYZE_DURATION:
                if filtered_distance >= self.SAFE_DISTANCE:
                    self.log_thought('SCAN', f'Clear path at {filtered_distance:.0f}cm → FORWARD', 'info')
                    logger.info(f"✅ Clear at {filtered_distance:.0f}cm - moving forward")
                    self._change_state('moving_forward')
                    self.consecutive_turns = 0
                    self.backup_count = 0
                elif filtered_distance >= self.CAUTION_DISTANCE:
                    self.log_thought('SCAN', f'Caution zone {filtered_distance:.0f}cm → SLOW', 'warning')
                    logger.info(f"⚠️ Caution at {filtered_distance:.0f}cm - slow forward")
                    self._change_state('slow_forward')
                else:
                    # Need to turn
                    self.log_thought('SCAN', f'Blocked at {filtered_distance:.0f}cm - need turn', 'warning')
                    if left_clear and not right_clear:
                        self._change_state('turning_left')
                    elif right_clear:
                        self._change_state('turning_right')
                    else:
                        new_dir = 'turning_left' if self.last_turn_direction == 'right' else 'turning_right'
                        self._change_state(new_dir)
            return command

        # STATE: MOVING FORWARD (normal speed)
        if self.navigation_state == 'moving_forward':
            if filtered_distance < self.CAUTION_DISTANCE:
                logger.info(f"⚠️ Obstacle approaching at {filtered_distance:.0f}cm - slowing")
                self._change_state('slow_forward')
                command['speed'] = self.slow_forward_speed
                command['action'] = 'slow_forward'
                self.last_action = 'slow_forward'
                return command

            command['speed'] = self.forward_speed
            command['action'] = 'forward'
            self.last_action = 'forward'

            if time_in_state >= self.MOVE_CHUNK_DURATION:
                self._change_state('analyzing')

            return command

        # STATE: SLOW FORWARD (caution)
        if self.navigation_state == 'slow_forward':
            if filtered_distance < self.DANGER_DISTANCE:
                logger.info(f"🛑 Too close at {filtered_distance:.0f}cm - stopping")
                self._change_state('analyzing')
                command['speed'] = 0
                command['action'] = 'stop'
                self.last_action = 'stop'
                return command

            command['speed'] = self.slow_forward_speed
            command['action'] = 'slow_forward'
            self.last_action = 'slow_forward'

            if time_in_state >= self.MOVE_CHUNK_DURATION:
                self._change_state('analyzing')

            return command

        # STATE: STOPPED
        if self.navigation_state == 'stopped':
            command['speed'] = 0
            command['action'] = 'stop'
            self.last_action = 'stop'

            if time_in_state >= 0.3:
                self._change_state('analyzing')

            return command

        # Fallback
        self.last_action = 'stop'
        self._change_state('analyzing')
        return command

    def _change_state(self, new_state: str):
        """Change navigation state and reset timer"""
        if new_state != self.navigation_state:
            self.previous_state = self.navigation_state
            self.navigation_state = new_state
            self.state_start_time = time.time()
            self.frames_in_state = 0
            logger.info(f"🔄 State: {self.previous_state} → {new_state}")

    def get_status(self) -> Dict:
        """Get current AI processor status for debugging"""
        return {
            'navigation_state': self.navigation_state,
            'previous_state': self.previous_state,
            'frames_in_state': self.frames_in_state,
            'frame_count': self.frame_count,
            'position': self.position,
            'last_turn': self.last_turn_direction,
            'consecutive_turns': self.consecutive_turns,
            'timing': {
                'move_chunk': self.MOVE_CHUNK_DURATION,
                'turn_chunk': self.TURN_CHUNK_DURATION,
                'analyze': self.ANALYZE_DURATION
            },
            'thresholds': {
                'danger': self.DANGER_DISTANCE,
                'caution': self.CAUTION_DISTANCE,
                'safe': self.SAFE_DISTANCE
            }
        }

    def reset(self):
        """Reset all state for fresh start"""
        self.navigation_state = 'analyzing'
        self.previous_state = None
        self.state_start_time = time.time()
        self.frames_in_state = 0
        self.consecutive_turns = 0
        self.escape_direction = 'right'
        self.last_turn_direction = 'right'
        self.last_action = 'stop'
        self.stuck_counter = 0
        self.is_currently_stuck = False
        self.backup_count = 0
        self.movement_history.clear()
        self.ultrasonic_history.clear()
        self.path_history.clear()
        self.obstacle_map = []
        self.position = {'x': 0, 'y': 0, 'heading': 0}
        self.previous_frame = None
        logger.info("🔄 AI Processor reset - starting in ANALYZING state")


# Singleton instance
processor = AIVideoProcessor()

