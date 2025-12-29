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
from ultralytics import YOLO
import torch
# Fix for PyTorch 2.6+ security changes
try:
    import ultralytics.nn.tasks
    torch.serialization.add_safe_globals([ultralytics.nn.tasks.DetectionModel])
except Exception as e:
    logging.warning(f"Could not add safe globals: {e}")

import os

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
        # States: 'analyzing', 'moving_forward', 'turning_left', 'turning_right', 'stopped', 'santa_approach', 'tracking_hat'
        self.navigation_state = 'analyzing'
        self.previous_state = None
        self.state_start_time = time.time()
        
        self.santa_mode_active = False
        self.christmas_tree_detected = False
        self.santa_hat_detected = False
        self.santa_standby = False
        self.santa_feedback_active = False
        self.santa_spotted_time = 0
        self.hat_position = None
        self.hat_is_close = False
        self.hat_persist_counter = 0 # Frames to keep hat "detected" if lost

        # Movement chunk timing (in seconds) - PLAN THEN EXECUTE
        self.MOVE_CHUNK_DURATION = 1.0    # Longer forward execution (was 0.5s)
        self.TURN_CHUNK_DURATION = 0.2    # Very short turns (~45 degrees at 70% power)
        self.BACKUP_DURATION = 0.6        # Short backup
        self.ANALYZE_DURATION = 0.4       # Longer pause to think before acting
        self.SCAN_DURATION = 0.5          # Duration for each scan side (left/right)

        # Turn tracking
        self.last_turn_direction = 'right'
        self.escape_direction = 'right'
        self.consecutive_turns = 0
        self.backup_count = 0  # Track how many times we've backed up

        # Frame processing
        self.previous_frame = None
        self.frame_count = 0
        self.frames_in_state = 0

        # Advanced Object Detection (YOLOv8)
        try:
            # Use nano model for performance
            self.model = YOLO('yolov8n.pt')
            self.yolo_enabled = True
            logger.info("✅ YOLOv8 Object Detection initialized")
        except Exception as e:
            logger.error(f"❌ Failed to load YOLOv8: {e}")
            self.yolo_enabled = False
        # Stuck detection - VISUAL based
        self.movement_history = deque(maxlen=10)
        self.stuck_counter = 0
        self.stuck_threshold = 2.5       # Increased sensitivity (was 1.5)
        self.stuck_frames_needed = 3     # Fewer frames needed (was 5)
        self.is_currently_stuck = False
        self.last_action = 'stop'        # Track what robot should be doing

        # Speed control - MINIMUM POWER for movement (50% floor, 70% carpet)
        self.forward_speed = 55           # 55% - works on floor
        self.slow_forward_speed = 50      # 50% - minimum for floor
        self.turn_speed = 70              # 70% - works on carpet
        self.gentle_turn_speed = 55       # 55% - gentle but functional
        self.backup_speed = 55            # 55% - reliable backup

        # Ultrasonic history for noise filtering (front and back)
        self.ultrasonic_history = deque(maxlen=5)
        self.ultrasonic_back_history = deque(maxlen=5)
        self.back_distance = 100  # Track back distance

        # Movement tracking for radar visualization
        self.position = {'x': 0, 'y': 0, 'heading': 0}
        self.path_history = deque(maxlen=100)
        self.obstacle_map = []

        # Distance thresholds (in cm) - CONSERVATIVE for safety
        self.TOO_CLOSE_DISTANCE = 25      # Increased from 20cm - stop earlier
        self.DANGER_DISTANCE = 45         # Increased from 35cm - more caution
        self.CAUTION_DISTANCE = 65        # Increased from 50cm - slow down earlier  
        self.SAFE_DISTANCE = 90           # Increased from 70cm - need more space

        # Lane keeping
        self.previous_lanes = None
        self.lane_history = deque(maxlen=10)

        # Exploration memory and bias
        self.exploration_bias = 0         # Positive = right, Negative = left
        self.stagnation_counter = 0        # Count frames without meaningful progress
        self.last_positions = deque(maxlen=30)  # History of positions for stagnation check
        self.exploration_mode = 'scout'    # 'scout', 'plan', 'escape'
        
        # Scan-and-Plan memory
        self.scan_results = {'left': 100.0, 'right': 100.0}
        self.scan_step = 0 # 0=none, 1=scanning_left, 2=scanning_right
        
        # Object detection settings
        self.min_object_area = 500  # Minimum contour area to consider (now mostly for fallback)
        self.detected_objects = []  # Store detected objects for overlay

        # Capture settings
        self.capture_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'captures', 'santa')
        if not os.path.exists(self.capture_dir):
            os.makedirs(self.capture_dir)
        self.last_capture_time = 0
        self.capture_cooldown = 10.0 # Seconds between captures
        
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

        # ONLY add Santa narration in Santa Mode
        if self.santa_mode_active:
            if self.santa_hat_detected:
                if self.navigation_state == 'santa_pickup':
                    narration = "Ho ho ho! Picking up this Santa Hat for the workshop! 🎅🎁"
                else:
                    narration = f"I've spotted a Santa Hat to the {self.hat_position}! I'm on its trail! 🎅"
            elif self.christmas_tree_detected:
                narration = "Ho ho ho! I've spotted a Christmas Tree! Delivering presents now! 🎄"
            elif 'red' in [o['type'].lower() for o in detected_objects]:
                narration = "Careful, there's a red gift in the way. I'll stay back to keep it safe. 🎁"
            elif 'green' in [o['type'].lower() for o in detected_objects]:
                narration = "I see a green decoration ahead. Better not disturb it! 🎄"
            else:
                narration = "Sleigh bells ring, are you listening? I'm scouting for the tree! 🎅"
        
        return narration

    def get_thinking_log(self) -> list:
        """Get the current thinking log as a list"""
        return list(self.thinking_log)

    def detect_objects(self, image: np.ndarray) -> List[Dict]:
        """
        Detect and classify objects in the image using YOLOv8 and contour analysis.
        Returns list of detected objects with bounding boxes and classifications.
        """
        if image is None:
            self.detected_objects = []
            return []

        height, width = image.shape[:2]

        # --- STEP 1: YOLOv8 INFERENCE ---
        # ONLY run YOLO in AI Auto mode (not Santa Mode) for performance
        yolo_results = []
        if self.yolo_enabled and not self.santa_mode_active:
            # Use HIGH confidence threshold (0.6) to avoid false positives
            results = self.model(image, stream=True, verbose=False, conf=0.6)
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    # Get box coordinates, class, and confidence
                    b = box.xyxy[0].tolist() 
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    # DOUBLE-CHECK: Only accept high-confidence detections
                    if conf < 0.6:
                        continue
                        
                    name = self.model.names[cls].upper()
                    
                    x1, y1, x2, y2 = b
                    bw, bh = x2 - x1, y2 - y1
                    bcx, bcy = (x1 + x2) / 2, (y1 + y2) / 2
                    
                    # Determine position
                    pos = 'center'
                    if bcx < width // 3: pos = 'left'
                    elif bcx > 2 * width // 3: pos = 'right'
                    
                    # Distance estimate
                    v_pos = bcy / height
                    s_fact = (bw * bh) / (width * height)
                    dist = 'far'
                    if v_pos > 0.6 or s_fact > 0.1: dist = 'close'
                    elif v_pos > 0.4 or s_fact > 0.05: dist = 'medium'
                    
                    yolo_results.append({
                        'type': name,
                        'confidence': conf,
                        'bbox': [int(x1), int(y1), int(bw), int(bh)],
                        'center': [int(bcx), int(bcy)],
                        'position': pos,
                        'distance': dist,
                        'color': (255, 255, 0) # Cyan for YOLO objects
                    })

        # --- STEP 2: CUSTOM SANTA HAT & FALLBACK CONTOUR LOGIC ---
        # (This handles things YOLO might miss, like the specific Santa Hat, or generic obstacles)
        detected = yolo_results # Start with YOLO findings
        
        # Pre-process for contours
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for c in contours:
            area = cv2.contourArea(c)
            # IGNORE VERY SMALL NOISE, but include small objects (lowered to 400)
            if area < 400: continue
            
            x, y, w, h = cv2.boundingRect(c)
            cx, cy = x + w // 2, y + h // 2

            # Calculate solidity EARLY for filtering
            solidity = 0
            hull = cv2.convexHull(c)
            hull_area = cv2.contourArea(hull)
            if hull_area > 0:
                solidity = float(area) / hull_area
            
            # AGGRESSIVE FLOOR FILTERING for contour-based detection
            # Camera is angled low - bottom 75% is mostly floor
            # Increased from 68% to 75% to filter more floor noise
            is_hat = False
            if self.santa_hat_detected and self.hat_bbox:
                hx, hy, hw, hh = self.hat_bbox
                if abs(cx - (hx + hw//2)) < 50 and abs(cy - (hy + hh//2)) < 50:
                    is_hat = True

            bottom_threshold = height * 0.75  # Increased from 0.68
            if cy > bottom_threshold and not is_hat:
                continue
            
            # ADDITIONAL: For objects in lower half (50-75%), require higher confidence
            # This prevents floor reflections from being detected as obstacles
            lower_half_threshold = height * 0.50
            if cy > lower_half_threshold and cy <= bottom_threshold:
                # In lower half - check if this looks like a real obstacle
                # Skip if it's too small or has low solidity (likely reflection/shadow)
                if area < 800 or solidity < 0.6:
                    continue

            # Skip if too small or too large
            if w < 30 or h < 30 or w > width * 0.9 or h > height * 0.9:
                continue

            # Check if this area is already covered by a high-confidence YOLO box
            is_duplicate = False
            for yr in yolo_results:
                yb = yr['bbox']
                # Check for significant overlap (e.g., 70% overlap in area or center proximity)
                # For simplicity, check if contour bbox is largely contained within YOLO bbox
                if x > yb[0]-10 and y > yb[1]-10 and x+w < yb[0]+yb[2]+10 and y+h < yb[1]+yb[3]+10:
                    is_duplicate = True
                    break
            if is_duplicate: continue

            # Determine position
            position = 'center'
            if cx < width // 3: position = 'left'
            elif cx > 2 * width // 3: position = 'right'
            else: position = 'center'

            # Calculate shape properties for classification
            aspect_ratio = float(w) / h
            # Solidity already calculated above

            # SPECIAL CHECK: Is this the Santa Hat?
            if self.santa_hat_detected and self.hat_bbox:
                hx, hy, hw, hh = self.hat_bbox
                # If centers are very close, it's the hat!
                if abs(cx - (hx + hw//2)) < 40 and abs(cy - (hy + hh//2)) < 40:
                    obj_type, confidence, color = ('SANTA HAT', 1.0, (255, 255, 255))
                else:
                    obj_type, confidence, color = self._classify_object(
                        area, aspect_ratio, 0, solidity, None, w, h, cy, height
                    )
            else:
                # Normal classification
                obj_type, confidence, color = self._classify_object(
                    area, aspect_ratio, 0, solidity, None, w, h, cy, height
                )

            # Map distance
            v_pos = cy / height
            s_fact = (w * h) / (width * height)
            dist_est = 'far'
            if v_pos > 0.6 or s_fact > 0.1: dist_est = 'close'
            elif v_pos > 0.4 or s_fact > 0.05: dist_est = 'medium'

            detected.append({
                'type': obj_type,
                'confidence': confidence,
                'bbox': [x, y, w, h],
                'center': [cx, cy],
                'position': position,
                'distance': dist_est,
                'area': area,
                'color': color
            })

        # Sort by area (largest first) and limit to top 10
        detected.sort(key=lambda x: x.get('area', 0), reverse=True)
        self.detected_objects = detected[:10] # Track more objects now that it's stable
        return self.detected_objects

    def _classify_object(self, area, aspect_ratio, extent, solidity,
                         vertices, w, h, cy, img_height) -> Tuple[str, float, Tuple[int, int, int]]:
        """
        Classify detected object based on shape properties.
        Specifically tuned for Windows, Doors, and Furniture.
        """
        # --- DOORS ---
        # Tall, rectangular, solid, often spans significant height
        if 0.4 < aspect_ratio < 0.8 and h > img_height * 0.5 and solidity > 0.8:
            return ('DOOR', 0.85, (100, 255, 100))  # Bright Green

        # --- WINDOWS ---
        # Rectangular, higher up in the frame, often high contrast/bright
        if 0.8 < aspect_ratio < 2.0 and cy < img_height * 0.4 and solidity > 0.8:
            return ('WINDOW', 0.8, (255, 255, 100))  # Light Blue/Cyan-ish

        # Wall/Large obstacle - wide, spans bottom/middle
        if aspect_ratio > 2.0 and extent > 0.5 and cy > img_height * 0.3:
            return ('WALL', 0.8, (0, 0, 255))  # Red

        # Box/Furniture - roughly square, high solidity
        if 0.7 < aspect_ratio < 1.4 and solidity > 0.8:
            return ('FURNITURE', 0.75, (255, 128, 0))  # Orange

        # Small object
        if area < 2000:
            return ('SMALL OBJ', 0.5, (128, 255, 128))  # Light green

        # --- CHRISTMAS TREE ---
        # Very large, upright object, usually tapered (not a wall)
        if area > 15000 and 0.5 < aspect_ratio < 1.0 and solidity > 0.6:
            return ('CHRISTMAS TREE', 0.9, (0, 100, 0)) # Dark Green

        # Generic obstacle
        return ('OBSTACLE', 0.6, (0, 200, 200))  # Cyan

    def detect_festive_colors(self, image: np.ndarray) -> Dict[str, bool]:
        """Detect presence of red and green colors for Santa Mode"""
        if image is None:
            return {'red': False, 'green': False, 'tree': False}
            
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Green range (Christmas Tree / Evergreen) - focus on saturation
        lower_green = np.array([40, 60, 40])
        upper_green = np.array([85, 255, 255])
        mask_green = cv2.inRange(hsv, lower_green, upper_green)
        green_pixel_ratio = np.count_nonzero(mask_green) / mask_green.size
        
        # Red range (Santa / Ornaments) - robust hue wrapping
        lower_red1 = np.array([0, 90, 60])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 90, 60])
        upper_red2 = np.array([180, 255, 255])
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)
        red_pixel_ratio = np.count_nonzero(mask_red) / mask_red.size
        
        return {
            'red': red_pixel_ratio > 0.012,       # Lowered to 1.2%
            'green': green_pixel_ratio > 0.012,   # Lowered to 1.2%
            'tree': green_pixel_ratio > 0.08      # Lowered to 8% (detect tree sooner)
        }

    def _detect_santa_hat(self, image: np.ndarray) -> Tuple[bool, str]:
        """Detect Santa Hat by looking for red contours with white tips"""
        if image is None:
            return False, None
            
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Red mask - DRASTICALLY LOOSENED for indoor lighting
        # Saturation down to 60, Value down to 40
        lower_red1 = np.array([0, 60, 40])
        upper_red1 = np.array([12, 255, 255])
        lower_red2 = np.array([155, 60, 40])
        upper_red2 = np.array([180, 255, 255])
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)
        
        contours, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) == 0:
            logger.debug("🎅 No red contours found in Hat detector.")
            
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 600: continue 
            
            x, y, w, h = cv2.boundingRect(cnt)
            logger.debug(f"🎅 Found red contour area={area:.0f} at x={x},y={y}")
            # Pom-pom check - check TOP 30% or ABOVE
            pom_roi_y = max(0, y - 30)
            roi_h = min(image.shape[0] - pom_roi_y, h // 2 + 30)
            roi = image[pom_roi_y:pom_roi_y+roi_h, x:x+w]
            
            if roi.size == 0: continue
            
            # White detection - LOOSENED
            # Value down to 130
            hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            mask_white = cv2.inRange(hsv_roi, np.array([0, 0, 130]), np.array([180, 90, 255]))
            white_ratio = np.count_nonzero(mask_white) / mask_white.size
            
            logger.debug(f"🎅 Pom-pom white ratio: {white_ratio:.2f}")

            # Fallback: If it's a Red object, trust it as a potential hat even if small
            # LOOSENED thresholds: area > 1200 (was 10000)
            if white_ratio > 0.04 or area > 1200: 
                cx = x + w // 2
                cy = y + h // 2
                
                # Add hysteresis to positioning to prevent jitter
                # Use a wider center band (25% to 75% instead of 33% to 66%)
                width = image.shape[1]
                left_bound = width * 0.4
                right_bound = width * 0.6
                
                # If was already in a state, use a wider margin to stay in it
                if hasattr(self, 'hat_position') and self.hat_position:
                    if self.hat_position == 'left': left_bound += 40
                    if self.hat_position == 'right': right_bound -= 40
                
                pos = 'center'
                if cx < left_bound: pos = 'left'
                elif cx > right_bound: pos = 'right'
                
                # Check vertical position - if it's in the lower part of the screen, it's close
                is_close = cy > image.shape[0] * 0.55
                return True, pos, is_close, (x, y, w, h)
                
        return False, None, False, None

    def _detect_high_confidence_center_obstacles(self, image: np.ndarray) -> List[Dict]:
        """
        Detect ONLY high-confidence (>90%) obstacles in the CENTER of the frame.
        Used during execution phase to avoid false positives from vision.
        
        Returns:
            List of high-confidence center obstacles
        """
        if image is None or not self.yolo_enabled:
            return []
        
        height, width = image.shape[:2]
        center_obstacles = []
        
        # Use VERY HIGH confidence threshold (0.9 = 90%)
        results = self.model(image, stream=True, verbose=False, conf=0.9)
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                b = box.xyxy[0].tolist()
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                
                # Only accept 90%+ confidence
                if conf < 0.9:
                    continue
                
                x1, y1, x2, y2 = b
                cx = (x1 + x2) / 2
                
                # Only accept objects in CENTER 30% of frame
                left_bound = width * 0.35
                right_bound = width * 0.65
                
                if left_bound < cx < right_bound:
                    name = self.model.names[cls].upper()
                    center_obstacles.append({
                        'type': name,
                        'confidence': conf,
                        'center_x': cx,
                        'bbox': [int(x1), int(y1), int(x2-x1), int(y2-y1)]
                    })
        
        return center_obstacles

    def _capture_santa_image(self, image: np.ndarray, label: str = "santa"):
        """Capture and save an image to the captures directory"""
        now = time.time()
        if now - self.last_capture_time < self.capture_cooldown:
            return False
            
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{label}_{timestamp}.jpg"
        filepath = os.path.join(self.capture_dir, filename)
        
        try:
            cv2.imwrite(filepath, image)
            self.last_capture_time = now
            self.log_thought('CAPTURE', f'Saved Santa image: {filename}', 'success')
            logger.info(f"📸 Captured image: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            return False

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
            self.stuck_counter = 0
            return False

        if len(self.movement_history) < 3:
            return False

        # Get recent frame differences
        recent = list(self.movement_history)[-self.stuck_frames_needed:]
        avg_movement = np.mean(recent)

        # If image isn't changing much while we should be moving → stuck!
        if avg_movement < self.stuck_threshold:
            self.stuck_counter += 1
            if self.stuck_counter >= self.stuck_frames_needed:
                if not self.is_currently_stuck:
                    self.log_thought('STUCK', f'Not moving (diff={avg_movement:.1f})', 'danger')
                self.is_currently_stuck = True
                return True
        else:
            self.stuck_counter = max(0, self.stuck_counter - 1)
            if self.stuck_counter == 0:
                self.is_currently_stuck = False

        return self.is_currently_stuck

    def check_stagnation(self) -> bool:
        """
        Check if the robot is stagnant (not making progress over time)
        Even if not physically stuck, it might be in an 'infinite loop'
        """
        self.last_positions.append(self.position.copy())
        
        if len(self.last_positions) < 30:
            return False
            
        # Calculate spread of positions over last 30 samples (~3 seconds)
        xs = [p['x'] for p in self.last_positions]
        ys = [p['y'] for p in self.last_positions]
        
        spread = (max(xs) - min(xs)) + (max(ys) - min(ys))
        
        # If total movement spread is very small, we are stagnant
        if spread < 10:  # Very little total displacement
            self.stagnation_counter += 1
            if self.stagnation_counter > 50: # Persistently stagnant
                return True
        else:
            self.stagnation_counter = max(0, self.stagnation_counter - 5)
            
        return False

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
        
        # CLEAN UI - Distance sensors at top-left (ALWAYS VISIBLE)
        cv2.putText(result, f"Front: {front_distance:.0f}cm", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(result, f"Rear: {back_distance:.0f}cm", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # SANTA MODE BANNER - Only in Santa Mode
        if self.santa_mode_active:
            banner_h = 35
            cv2.rectangle(result, (0, height - banner_h), (width, height), (50, 50, 180), -1)
            cv2.putText(result, "🎅 SANTA MODE", (10, height - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            if self.christmas_tree_detected:
                cv2.putText(result, "🎄 TREE", (width - 100, height - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 100), 2)
            
            if self.santa_hat_detected:
                cv2.putText(result, "🎅 HAT", (width - 180, height - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return result

    def process_frame(self, base64_frame: str, ultrasonic_distance: float = 100,
                      ultrasonic_distance_back: float = 100, scan_direction: str = None,
                      imu_data: dict = None) -> Dict:
        """
        Process a single video frame with deliberate navigation.
        Uses front/back ultrasonic sensors and IMU data.
        
        Args:
            base64_frame: Base64 encoded image
            ultrasonic_distance: Front ultrasonic distance in cm
            ultrasonic_distance_back: Rear ultrasonic distance in cm
            scan_direction: Optional scan direction
            imu_data: IMU sensor data (accelerometer, gyroscope)
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

        # Store IMU data for navigation decisions
        self.imu_data = imu_data if imu_data else {}
        
        # CRITICAL SAFETY: Check for dangerous tilt using IMU
        if imu_data:
            accel = imu_data.get('accel', {})
            accel_x = abs(accel.get('x', 0))
            accel_y = abs(accel.get('y', 0))
            
            # If tilted >30 degrees (accel > 0.5g on X or Y), STOP immediately
            if accel_x > 0.5 or accel_y > 0.5:
                self.log_thought('SAFETY', f'TILT DETECTED! X={accel_x:.2f}g Y={accel_y:.2f}g - STOPPING', 'danger')
                logger.error(f"⚠️ CRITICAL TILT! Stopping for safety")
                return {
                    'processed_frame': self.image_to_base64(image),
                    'navigation_command': {
                        'action': 'stop',
                        'speed': 0,
                        'state': 'stopped',
                        'distance': front_distance,
                        'danger_zone': 'critical'
                    },
                    'narration': 'Safety stop - robot tilted!',
                    'distance': front_distance,
                    'back_distance': back_distance
                }
        
        # Detect frame change (for stuck detection)
        frame_change = self.detect_movement(image)

        # Santa Mode processing - ONLY in Santa Mode
        if self.santa_mode_active:
            festive_data = self.detect_festive_colors(image)
            self.christmas_tree_detected = festive_data['tree']
            
            # Santa Hat Detection (Red contour + White pom-pom)
            hat_detected, hat_pos, hat_close, hat_bbox = self._detect_santa_hat(image)
            if hat_detected:
                self.santa_hat_detected = True
                self.hat_position = hat_pos
                self.hat_is_close = hat_close
                self.hat_bbox = hat_bbox
                self.hat_persist_counter = 5
            elif self.hat_persist_counter > 0:
                self.hat_persist_counter -= 1
            else:
                self.santa_hat_detected = False
                self.hat_position = None
                self.hat_bbox = None
                
            if self.santa_hat_detected:
                self.log_thought('SANTA', f'HAT DETECTED! Position: {self.hat_position}', 'success')
        else:
            # AI Auto Mode - NO Santa detection
            self.christmas_tree_detected = False
            self.santa_hat_detected = False
            self.hat_position = None
            self.hat_bbox = None

        if self.santa_standby:
            # Check for PERSON or SANTA HAT in center
            for obj in self.detected_objects:
                if (obj['type'] == 'PERSON' or obj['type'] == 'SANTA HAT') and obj['position'] == 'center':
                    if self._capture_santa_image(image, obj['type'].lower()):
                        self.log_thought('SANTA', f'🎅 SANTA SPOTTED! ({obj["type"]}) 📸', 'success')
                        self.santa_spotted_time = time.time()
                    break

        # Pulse feedback duration management
        if hasattr(self, 'santa_spotted_time') and time.time() - self.santa_spotted_time < 3.0:
            self.santa_feedback_active = True
        else:
            self.santa_feedback_active = False

        # Santa Mode specific processing
        if self.santa_mode_active:
            if self.christmas_tree_detected and not self.santa_hat_detected:
                self.log_thought('SANTA', 'CHRISTMAS TREE SPOTTED! Approaching...', 'success')
            elif (festive_data['red'] or festive_data['green']) and not self.santa_hat_detected:
                self.log_thought('SANTA', 'Festive colors detected - staying back.', 'warning')
                # If we aren't already backing up, force an analyze to decide
                if self.navigation_state in ['moving_forward', 'slow_forward']:
                    self._change_state('analyzing')

        # ============================================================
        # STATE-BASED VISION PROCESSING (Plan-Then-Execute)
        # ============================================================
        
        # Initialize default obstacle data
        if not hasattr(self, 'smoothed_densities'):
            self.smoothed_densities = {'left': 0, 'center': 0, 'right': 0}
            
        obstacle_data = {}
        detected_objects = []

        # PLANNING PHASE: Thorough analysis while stopped/analyzing
        if self.navigation_state in ['analyzing', 'stopped', 'scanning_left', 'scanning_right']:
            # 1. Full Obstacle Detection (Edge based)
            raw_obstacle_data = self._detect_obstacles_simple(image, front_distance)
            
            # Smooth the results
            alpha = 0.4
            self.smoothed_densities['left'] = alpha * raw_obstacle_data['left_density'] + (1-alpha) * self.smoothed_densities['left']
            self.smoothed_densities['center'] = alpha * raw_obstacle_data['center_density'] + (1-alpha) * self.smoothed_densities['center']
            self.smoothed_densities['right'] = alpha * raw_obstacle_data['right_density'] + (1-alpha) * self.smoothed_densities['right']

            # Set flags based on smoothed density
            threshold = 15
            obstacle_data['left_density'] = self.smoothed_densities['left']
            obstacle_data['center_density'] = self.smoothed_densities['center'] 
            obstacle_data['right_density'] = self.smoothed_densities['right']
            obstacle_data['left_clear'] = self.smoothed_densities['left'] < threshold
            obstacle_data['right_clear'] = self.smoothed_densities['right'] < threshold
            obstacle_data['center_blocked'] = self.smoothed_densities['center'] > threshold
            
            # 2. Full Object Detection (YOLO + Contours)
            detected_objects = self.detect_objects(image)
            
            self.log_thought('PLANNING', f'Full scan: {len(detected_objects)} objects, Blocked={obstacle_data["center_blocked"]}', 'info')

        # EXECUTION PHASE: Moving/Turning - Minimal Vision
        else:
            # 1. Decay smoothed densities (we aren't updating them with vision data)
            # This ensures old vision data fades away during execution
            decay = 0.8
            self.smoothed_densities['left'] *= decay
            self.smoothed_densities['center'] *= decay
            self.smoothed_densities['right'] *= decay
            
            # 2. ULTRASONIC IS PRIMARY
            # We assume clear unless ultrasonic says otherwise (handled in logic later)
            # or high-confidence vision says stop
            
            # 3. High-Confidence Center Obstacles ONLY
            high_conf = self._detect_high_confidence_center_obstacles(image)
            detected_objects = high_conf
            
            # Only trigger vision block if object is CONFIDENT + CLOSE
            # Use raw vision density = 0 since we skipped edge detection
            obstacle_data['left_density'] = 0
            obstacle_data['center_density'] = 0
            obstacle_data['right_density'] = 0
            obstacle_data['left_clear'] = True
            obstacle_data['right_clear'] = True
            
            # Check for vision based block
            vision_blocked = False
            for obj in high_conf:
                 # Calculate approximate distance based on bbox width/height if not available?
                 # detect_objects does this, but _detect_high_confidence doesn't call estimate_distance yet
                 # Let's simple assume if it's big enough in center, it's an issue
                 bbox_w = obj['bbox'][2]
                 if bbox_w > width * 0.2: # Takes up > 20% width
                     vision_blocked = True
                     break
            
            obstacle_data['center_blocked'] = vision_blocked
            
            if vision_blocked:
                self.log_thought('VISION', f'Override: High-conf obstacle detected!', 'warning')
            else:
                self.log_thought('EXECUTION', 'Ultrasonic-primary navigation', 'info')

        # Log detected objects if any close ones found
        close_objects = [o for o in detected_objects if o['distance'] == 'close']
        if close_objects and self.frame_count % 5 == 0:  # Log every 5th frame to reduce spam
            obj_summary = ', '.join([f"{o['type']}({o['position']})" for o in close_objects[:3]])
            self.log_thought('DETECT', f'Close objects: {obj_summary}', 'warning')

        # Generate navigation command
        nav_command = self._generate_deliberate_command(detected_objects, obstacle_data, front_distance, frame_change)

        # Create CLEAN overlay with object detection (not cluttered)
        clean_overlay = self._draw_clean_overlay(image, nav_command, front_distance, back_distance)

        # Update position tracking for radar
        self.update_position(nav_command['speed'], nav_command.get('turn'), 0.1)

        # Convert to base64
        processed_base64 = self.image_to_base64(clean_overlay)

        # Generate natural language narration
        narration = self.generate_narration(nav_command, detected_objects, front_distance, back_distance)

        # Override action for Santa spotted pulse feedback
        if self.santa_feedback_active:
            nav_command['action'] = 'santa_spotted'

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
        detected_objects: List[Dict],
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
            self.log_thought('STUCK', f'Physical obstruction - Backing up!', 'danger')
            self._change_state('backing_up')
            self.stuck_counter = 0 
            command['speed'] = self.backup_speed
            command['action'] = 'backup'
            command['is_stuck'] = True
            self.last_action = 'backup'
            
            # When stuck, flip the exploration bias to try a completely different direction
            self.exploration_bias = -self.exploration_bias
            return command

        # STAGNATON DETECTION (Infinite Loop Detection)
        if self.check_stagnation() and self.navigation_state not in ['backing_up', 'turning_left', 'turning_right']:
            self.log_thought('STAGNANT', 'Wandering in circles? Forcing rotation.', 'warning')
            self.stagnation_counter = 0
            self._change_state('turning_right') # Force a major course correction
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

        # TARGET LOCK-ON LOGIC
        # If we see a hat, shorten the decision cycle for frequent corrections
        is_tracking = self.santa_hat_detected or (self.santa_mode_active and self.christmas_tree_detected)
        current_chunk_duration = 0.4 if is_tracking else self.MOVE_CHUNK_DURATION
        current_turn_duration = 0.5 if is_tracking else self.TURN_CHUNK_DURATION

        # STATE: SCANNING LEFT
        if self.navigation_state == 'scanning_left':
            command['speed'] = self.turn_speed # Using reduced turn speed
            command['turn'] = 'left'
            command['action'] = 'turn_left'
            command['led_left'] = True
            
            # Record best distance seen during scan
            self.scan_results['left'] = min(self.scan_results['left'], filtered_distance)
            
            if time_in_state >= self.SCAN_DURATION:
                self.log_thought('SCAN', f'Left scan: {self.scan_results["left"]:.0f}cm', 'info')
                self._change_state('scanning_right')
            return command

        # STATE: SCANNING RIGHT
        if self.navigation_state == 'scanning_right':
            command['speed'] = self.turn_speed
            command['turn'] = 'right'
            command['action'] = 'turn_right'
            command['led_right'] = True
            
            # Record best distance seen during scan
            self.scan_results['right'] = min(self.scan_results['right'], filtered_distance)
            
            # Right scan needs to be longer to cross center and look right
            if time_in_state >= self.SCAN_DURATION * 1.8:
                self.log_thought('SCAN', f'Right scan: {self.scan_results["right"]:.0f}cm', 'info')
                
                # DECISION TIME
                if self.scan_results['left'] > self.scan_results['right'] + 10:
                    self.log_thought('PLAN', 'Left path looks better! Committing.', 'action')
                    self._change_state('turning_left')
                elif self.scan_results['right'] > self.scan_results['left'] + 10:
                    self.log_thought('PLAN', 'Right path looks better! Committing.', 'action')
                    self._change_state('turning_right')
                else:
                    # Too close to call - use exploration bias
                    target = 'turning_left' if self.exploration_bias > 0 else 'turning_right'
                    self.log_thought('PLAN', f'Paths similar, using bias → {target.split("_")[1].upper()}', 'info')
                    self._change_state(target)
            return command

        # STATE: BACKING UP
        if self.navigation_state == 'backing_up':
            # CRITICAL SAFETY: Check rear sensor during backup
            if self.back_distance < 15:
                self.log_thought('DANGER', f'Obstacle behind at {self.back_distance:.0f}cm - stopping backup!', 'danger')
                logger.warning(f"🚨 REAR OBSTACLE at {self.back_distance:.0f}cm - STOP BACKUP!")
                self._change_state('stopped')
                command['speed'] = 0
                command['action'] = 'stop'
                return command
                
            command['speed'] = self.backup_speed
            command['action'] = 'backup'
            command['led_left'] = True
            command['led_right'] = True
            self.last_action = 'backup'

            if time_in_state >= self.BACKUP_DURATION:
                logger.info(f"⏪ Backup complete ({self.BACKUP_DURATION}s)")
                self._change_state('analyzing')
                self.backup_count += 1

            return command  # Don't interrupt backup!

        # STATE: TURNING LEFT - committed, smoother power
        if self.navigation_state == 'turning_left':
            # DISABLED: Stuck spinning detection (was causing disconnections)
            # if hasattr(self, 'imu_data') and self.imu_data:
            #     gyro_z = abs(self.imu_data.get('gyro', {}).get('z', 0))
            #     if time_in_state > 2.0 and gyro_z > 100:
            #         self._change_state('backing_up')
                    
            command['speed'] = self.turn_speed  # 70% power
            command['turn'] = 'left'
            command['action'] = 'turn_left'
            command['led_left'] = True
            self.last_turn_direction = 'left'
            self.last_action = 'turn_left'

            if time_in_state >= current_turn_duration:
                logger.info(f"↩️ Left turn complete")
                self._change_state('analyzing')
                self.consecutive_turns += 1

            return command  # Don't interrupt turn!

        # STATE: TURNING RIGHT - committed, smoother power
        if self.navigation_state == 'turning_right':
            # DISABLED: Stuck spinning detection (was causing disconnections)
            # if hasattr(self, 'imu_data') and self.imu_data:
            #     gyro_z = abs(self.imu_data.get('gyro', {}).get('z', 0))
            #     if time_in_state > 2.0 and gyro_z > 100:
            #         self._change_state('backing_up')
                    
            command['speed'] = self.turn_speed
            command['turn'] = 'right'
            command['action'] = 'turn_right'
            command['led_right'] = True
            self.last_turn_direction = 'right'
            self.last_action = 'turn_right'

            if time_in_state >= current_turn_duration:
                logger.info(f"↪️ Right turn complete")
                self._change_state('analyzing')
                self.consecutive_turns += 1

            return command  # Don't interrupt turn!

        # STATE: AUTO PARKING
        if self.navigation_state == 'auto_parking':
            # 1. Safety Check - Rear
            if self.back_distance < 15:
                self.log_thought('SAFETY', f'Too close to rear wall ({self.back_distance:.0f}cm)! Stopping.', 'danger')
                command['speed'] = 0
                command['action'] = 'stop'
                return command
                
            # 2. Check Parking Condition (Wall < 30cm)
            if filtered_distance <= 30:
                self.log_thought('PARK', f'Parked safely at {filtered_distance:.0f}cm! 🅿️', 'success')
                logger.info(f"🅿️ Parked at {filtered_distance:.0f}cm")
                command['speed'] = 0
                command['action'] = 'stop'
                # Optionally turn on specific LEDs to indicate "Parked"
                command['led_left'] = True
                command['led_right'] = True
                return command
            
            # 3. Move Forward to Wall
            # Adaptive speed: Fast if far, Slow if close
            if filtered_distance > 80:
                 command['speed'] = self.forward_speed
                 command['action'] = 'forward'
                 self.log_thought('PARK', f'Approaching wall ({filtered_distance:.0f}cm)', 'action')
            else:
                 command['speed'] = self.slow_forward_speed
                 command['action'] = 'slow_forward'
                 self.log_thought('PARK', f'Precision docking ({filtered_distance:.0f}cm)', 'action')
            
            command['led_ai_mode'] = True # LED animation
            
            # 4. Simple centering/avoidance (optional)
            # If very close to side obstacles, maybe steer slightly?
            # For now, stick to the plan: "Drive forward until wall"
            
            if time_in_state > 0.5:
                # Re-analyze periodically to ensure we don't drift blindly? 
                pass

            return command

        # ============================================================
        # TARGET AWARENESS & OVERRIDES
        # ============================================================
        
        # If tracking a Santa Hat (all modes) or approaching a Tree (Santa mode)
        santa_override = self.santa_hat_detected or (self.santa_mode_active and self.christmas_tree_detected)
        
        # Santa override allows CLOSER approach but NOT bypassing obstacles entirely!
        # We still respect physical obstacles, just with a tighter threshold

        # ============================================================
        # DANGER CHECKS (only when not in committed action)
        # ============================================================
        
        # TOO CLOSE - Must backup! (CRITICAL SAFETY)
        # ALWAYS respect minimum safe distance - NO EXCEPTIONS
        too_close_threshold = 12 if santa_override else self.TOO_CLOSE_DISTANCE
        if filtered_distance < too_close_threshold:
            # In Standby, NEVER move backward
            if self.santa_standby:
                command['speed'] = 0
                command['action'] = 'stop'
                self.log_thought('SAFETY', f'Standby mode - stopping at {filtered_distance:.0f}cm', 'warning')
                return command
                
            # CRITICAL: Always backup when too close, even when tracking
            self.log_thought('DANGER', f'TOO CLOSE! {filtered_distance:.0f}cm < {too_close_threshold}cm', 'danger')
            logger.warning(f"🚨 TOO CLOSE! {filtered_distance:.0f}cm - BACKING UP!")
            self._change_state('backing_up')
            command['speed'] = self.backup_speed
            command['action'] = 'backup'
            return command

        # ============================================================
        # SANTA PICKUP CHECK - Only if we see the hat, it's center, and it's close
        # ============================================================
        if self.santa_hat_detected and self.hat_position == 'center' and (filtered_distance < 15 or self.hat_is_close):
             if self.navigation_state != 'santa_pickup':
                 self.log_thought('SANTA', 'Hat is close and centered! Starting PICKUP! 🎅🎁', 'success')
                 self._change_state('santa_pickup')
             
             command['speed'] = 0
             command['action'] = 'pickup'
             return command

        # DANGER ZONE - Need to stop and decide
        danger_threshold = 20 if santa_override else self.DANGER_DISTANCE
        
        if filtered_distance < danger_threshold:
            # Check if we have ANY clear direction
            if not left_clear and not right_clear and not santa_override:
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

            # After brief stop, enter SCANNING sequence
            if time_in_state > 0.3:
                self.log_thought('SCAN', 'Entering Scan-and-Plan sequence', 'info')
                self.scan_results = {'left': 100.0, 'right': 100.0}
                self._change_state('scanning_left')
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
                # 1. SPECIAL MODES PRIORITY
                if self.auto_park_mode:
                    # Auto Park Mode: If clear or safe, start parking
                    if filtered_distance > 100: # Far from wall
                        self.log_thought('PARK', 'Searching for wall...', 'action')
                        self._change_state('auto_parking')
                    else:
                        self.log_thought('PARK', f'Wall detected at {filtered_distance:.0f}cm - Approach', 'action')
                        self._change_state('auto_parking')
                elif filtered_distance >= self.SAFE_DISTANCE:
                    self.log_thought('SCAN', f'Clear path at {filtered_distance:.0f}cm → FORWARD', 'info')
                    logger.info(f"✅ Clear at {filtered_distance:.0f}cm - moving forward")
                    self._change_state('moving_forward')
                    self.consecutive_turns = 0
                    self.backup_count = 0
                elif filtered_distance >= self.CAUTION_DISTANCE or santa_override:
                    if self.santa_hat_detected:
                         # Track hat in ALL AI modes
                          self.log_thought('SANTA', f'Tracking hat at {filtered_distance:.0f}cm ({self.hat_position})', 'success')
                         
                          # Use GENTLE turns when tracking to avoid overshooting
                          if self.hat_position == 'left': self._change_state('gentle_turn_left')
                          elif self.hat_position == 'right': self._change_state('gentle_turn_right')
                          else: 
                              # STANDBY: Only rotate, no approach
                              if self.santa_standby:
                                  self._change_state('analyzing') # Stay centered
                                  return command
                                  
                              # If centered, move forward to close distance slowly
                              if filtered_distance < 15 or self.hat_is_close:
                                  self._change_state('santa_pickup')
                              else:
                                  self._change_state('santa_approach')
                    elif self.santa_mode_active:
                        if self.christmas_tree_detected:
                             self.log_thought('SANTA', 'Tree found - staying on course!', 'success')
                             self._change_state('moving_forward')
                        else:
                            self.log_thought('SCAN', f'Caution zone {filtered_distance:.0f}cm → SLOW', 'warning')
                        logger.info(f"⚠️ Caution at {filtered_distance:.0f}cm - slow forward")
                        self._change_state('slow_forward')
                    else:
                        # If tracking a hat, use GENTLE turns
                        if self.santa_hat_detected:
                            if self.hat_position == 'left': self._change_state('gentle_turn_left')
                            else: self._change_state('gentle_turn_right')
                            return command
                            
                        self.log_thought('SCAN', f'Caution zone {filtered_distance:.0f}cm → SLOW', 'warning')
                        logger.info(f"⚠️ Caution at {filtered_distance:.0f}cm - slow forward")
                        self._change_state('slow_forward')
                else:
                    # Generic blocked behavior
                    self.log_thought('SCAN', f'Blocked at {filtered_distance:.0f}cm - need turn', 'warning')
                    
                    # SANTA MODE: If we see festive colors but NOT a tree/hat, backup!
                    if self.santa_mode_active and not self.christmas_tree_detected and not self.santa_hat_detected:
                        self.log_thought('SANTA', 'Festive obstacle detected - backing up.', 'warning')
                        self._change_state('backing_up')
                    # CRITICAL: Check if BOTH sides are blocked
                    if not left_clear and not right_clear:
                        # COMPLETELY BLOCKED - Must backup to find space
                        self.log_thought('BLOCKED', 'Both sides blocked - backing up to reassess', 'danger')
                        logger.warning(f"🚨 BOTH SIDES BLOCKED - BACKING UP!")
                        self._change_state('backing_up')
                    elif left_clear and not right_clear:
                        self._change_state('turning_left')
                    elif right_clear and not left_clear:
                        self._change_state('turning_right')
                    else:
                        # Both clear but blocked ahead - pick a direction
                        new_dir = 'turning_left' if self.last_turn_direction == 'right' else 'turning_right'
                        self._change_state(new_dir)
            return command

        # STATE: MOVING FORWARD (normal speed)
        if self.navigation_state == 'moving_forward':
            # Preserve speed if tracking a hat/tree even in caution zone
            caution_limit = 20 if santa_override else self.CAUTION_DISTANCE
            if filtered_distance < caution_limit:
                logger.info(f"⚠️ Obstacle approaching at {filtered_distance:.0f}cm - slowing")
                self._change_state('slow_forward')
                command['speed'] = self.slow_forward_speed
                command['action'] = 'slow_forward'
                self.last_action = 'slow_forward'
                return command

            command['speed'] = self.forward_speed
            command['action'] = 'forward'
            self.last_action = 'forward'

            if time_in_state >= current_chunk_duration:
                # SANTA MODE CHECK
                if self.santa_mode_active and self.christmas_tree_detected:
                    # Move closer to the tree, but stop when very close
                    if filtered_distance < 15:
                        self.log_thought('SANTA', 'Arrived at the Christmas Tree! 🎄', 'success')
                        self._change_state('analyzing')
                    else:
                        self._change_state('moving_forward')
                elif self.santa_hat_detected:
                    # Keep moving forward if centered
                    if self.hat_position == 'center':
                        self._change_state('moving_forward')
                    else:
                        self._change_state('analyzing')
                else:
                    # PERSPECTIVE RETREAT - ONLY if NOT tracking anything
                    import random
                    if random.random() < 0.2:
                        self.log_thought('VISION', 'Backing up to see more of the room', 'info')
                        self._change_state('backing_up')
                    else:
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
                # Also retreat from slow forward occasionally
                import random
                if random.random() < 0.1:
                    self._change_state('backing_up')
                else:
                    self._change_state('analyzing')

            return command

        # STATE: GENTLE TURN LEFT (for precise tracking)
        if self.navigation_state == 'gentle_turn_left':
            command['speed'] = self.gentle_turn_speed
            command['action'] = 'gentle_turn_left'
            command['turn'] = -1
            self.last_turn_direction = 'left'
            self.last_action = 'gentle_turn_left'

            if time_in_state >= 0.4:  # Shorter duration for gentle corrections
                logger.info(f"↩️ Gentle left turn complete")
                self._change_state('analyzing')
                self.consecutive_turns += 1

            return command

        # STATE: GENTLE TURN RIGHT (for precise tracking)
        if self.navigation_state == 'gentle_turn_right':
            command['speed'] = self.gentle_turn_speed
            command['action'] = 'gentle_turn_right'
            command['turn'] = 1
            self.last_turn_direction = 'right'
            self.last_action = 'gentle_turn_right'

            if time_in_state >= 0.4:  # Shorter duration for gentle corrections
                logger.info(f"↪️ Gentle right turn complete")
                self._change_state('analyzing')
                self.consecutive_turns += 1

            return command

        # STATE: STOPPED
        if self.navigation_state == 'stopped':
            command['speed'] = 0
            command['action'] = 'stop'
            self.last_action = 'stop'

            if time_in_state >= 0.3:
                self._change_state('analyzing')

            return command

        # STATE: SANTA PICKUP
        if self.navigation_state == 'santa_pickup':
            command['speed'] = 0
            command['action'] = 'pickup'
            self.last_action = 'stop' 
            
            # Stay in this state for duration of pickup routine (approx 8 seconds)
            if time_in_state >= 8.0:
                self.log_thought('SANTA', 'Pickup attempt complete! Re-analyzing.', 'info')
                self._change_state('analyzing')
            return command

        # STATE: SANTA APPROACH (steady, slow)
        if self.navigation_state == 'santa_approach':
            command['speed'] = self.slow_forward_speed
            command['action'] = 'slow_forward'
            self.last_action = 'slow_forward'
            
            # Short chunks for frequent correction
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
        self.exploration_bias = 0
        self.stagnation_counter = 0
        self.last_positions.clear()
        self.exploration_mode = 'scout'
        self.last_positions.clear()
        self.exploration_mode = 'scout'
        self.scan_results = {'left': 100.0, 'right': 100.0}
        self.scan_step = 0
        self.auto_park_mode = False
        logger.info("🔄 AI Processor reset - starting in ANALYZING state")


# Singleton instance
processor = AIVideoProcessor()

