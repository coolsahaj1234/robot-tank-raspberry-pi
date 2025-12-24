#!/usr/bin/env python3
"""
AI Video Processing Service
Processes video frames for lane detection, obstacle detection, and path planning
"""

import cv2
import numpy as np
import base64
import json
from typing import Dict, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIVideoProcessor:
    """Processes video frames for autonomous navigation"""
    
    def __init__(self):
        self.previous_lanes = None
        self.turn_direction = None  # 'left', 'right', or None
        
    def base64_to_image(self, base64_string: str) -> np.ndarray:
        """Convert base64 string to OpenCV image"""
        try:
            # Remove data URL prefix if present
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            image_data = base64.b64decode(base64_string)
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            logger.error(f"Error decoding base64 image: {e}")
            return None
    
    def image_to_base64(self, image: np.ndarray) -> str:
        """Convert OpenCV image to base64 string"""
        try:
            _, buffer = cv2.imencode('.jpg', image)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            return image_base64
        except Exception as e:
            logger.error(f"Error encoding image to base64: {e}")
            return None
    
    def detect_lanes(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], Dict]:
        """
        Detect lanes in the image using edge detection and Hough transform
        Returns processed image with lane overlays and lane detection data
        """
        if image is None:
            return None, {}
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection using Canny
        edges = cv2.Canny(blurred, 50, 150)
        
        # Create region of interest (lower half of image for lane detection)
        height, width = edges.shape
        roi_vertices = np.array([[
            (0, height),
            (width // 2 - width // 4, height // 2),
            (width // 2 + width // 4, height // 2),
            (width, height)
        ]], dtype=np.int32)
        
        mask = np.zeros_like(edges)
        cv2.fillPoly(mask, roi_vertices, 255)
        masked_edges = cv2.bitwise_and(edges, mask)
        
        # Hough transform for line detection
        lines = cv2.HoughLinesP(
            masked_edges,
            rho=1,
            theta=np.pi/180,
            threshold=50,
            minLineLength=50,
            maxLineGap=100
        )
        
        # Create overlay image
        overlay = image.copy()
        lane_data = {
            'left_lane': None,
            'right_lane': None,
            'center_offset': 0,
            'turn_direction': None
        }
        
        if lines is not None:
            left_lines = []
            right_lines = []
            
            for line in lines:
                x1, y1, x2, y2 = line[0]
                slope = (y2 - y1) / (x2 - x1) if (x2 - x1) != 0 else 0
                
                # Filter lines by slope (lanes should be roughly vertical)
                if abs(slope) > 0.3:
                    if slope < 0:  # Left lane
                        left_lines.append(line[0])
                    else:  # Right lane
                        right_lines.append(line[0])
            
            # Draw left lane
            if left_lines:
                left_points = np.array(left_lines).reshape(-1, 2)
                if len(left_points) > 0:
                    cv2.polylines(overlay, [left_points], False, (0, 255, 0), 3)
                    lane_data['left_lane'] = left_points.tolist()
            
            # Draw right lane
            if right_lines:
                right_points = np.array(right_lines).reshape(-1, 2)
                if len(right_points) > 0:
                    cv2.polylines(overlay, [right_points], False, (0, 255, 0), 3)
                    lane_data['right_lane'] = right_points.tolist()
            
            # Calculate center offset
            if left_lines and right_lines:
                left_center = np.mean([x for line in left_lines for x in [line[0], line[2]]])
                right_center = np.mean([x for line in right_lines for x in [line[0], line[2]]])
                image_center = width / 2
                lane_center = (left_center + right_center) / 2
                offset = lane_center - image_center
                lane_data['center_offset'] = float(offset)
                
                # Determine turn direction
                if abs(offset) > 30:  # Significant offset
                    lane_data['turn_direction'] = 'left' if offset < 0 else 'right'
        
        # Draw center line
        cv2.line(overlay, (width // 2, height), (width // 2, height // 2), (255, 0, 0), 2)
        
        # Draw predicted path (green curve)
        if lane_data['left_lane'] and lane_data['right_lane']:
            # Simple path prediction: curve towards lane center
            path_points = []
            for y in range(height, height // 2, -10):
                t = (height - y) / (height / 2)
                x = width // 2 + lane_data['center_offset'] * t * 0.5
                path_points.append([int(x), y])
            
            if path_points:
                pts = np.array(path_points, np.int32)
                cv2.polylines(overlay, [pts], False, (0, 255, 255), 3)
        
        return overlay, lane_data
    
    def detect_obstacles(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], Dict]:
        """
        Detect obstacles (walls, objects) in the image
        Returns processed image with obstacle overlays and obstacle data
        """
        if image is None:
            return None, {}
        
        overlay = image.copy()
        obstacle_data = {
            'obstacles': [],
            'nearest_obstacle': None,
            'obstacle_distance': None,
            'should_turn': False,
            'turn_direction': None
        }
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Detect walls/obstacles using edge detection and contour analysis
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        height, width = image.shape[:2]
        center_x = width // 2
        
        # Analyze contours in the forward path (center region)
        forward_region_y = height // 2
        obstacles_in_path = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # Filter small noise
                x, y, w, h = cv2.boundingRect(contour)
                center_contour_x = x + w // 2
                
                # Check if obstacle is in forward path
                if y < forward_region_y and abs(center_contour_x - center_x) < width // 3:
                    obstacles_in_path.append({
                        'x': int(x),
                        'y': int(y),
                        'width': int(w),
                        'height': int(h),
                        'center_x': int(center_contour_x),
                        'area': float(area)
                    })
                    
                    # Draw obstacle bounding box
                    cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.putText(overlay, 'OBSTACLE', (x, y - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        if obstacles_in_path:
            # Find nearest obstacle
            nearest = min(obstacles_in_path, key=lambda o: o['y'])
            obstacle_data['nearest_obstacle'] = nearest
            obstacle_data['obstacles'] = obstacles_in_path
            
            # Estimate distance (simplified: closer to bottom = closer to robot)
            distance_estimate = (height - nearest['y']) / height * 100  # Percentage
            obstacle_data['obstacle_distance'] = distance_estimate
            
            # Determine if we should turn
            if distance_estimate < 40:  # Close obstacle
                obstacle_data['should_turn'] = True
                # Turn away from obstacle center
                if nearest['center_x'] < center_x:
                    obstacle_data['turn_direction'] = 'right'
                else:
                    obstacle_data['turn_direction'] = 'left'
        
        return overlay, obstacle_data
    
    def process_frame(self, base64_frame: str) -> Dict:
        """
        Process a single video frame
        Returns processed frame and detection data
        """
        # Decode image
        image = self.base64_to_image(base64_frame)
        if image is None:
            return None
        
        # Process lane detection
        lane_overlay, lane_data = self.detect_lanes(image)
        
        # Process obstacle detection
        obstacle_overlay, obstacle_data = self.detect_obstacles(image)
        
        # Combine overlays
        if lane_overlay is not None and obstacle_overlay is not None:
            combined_overlay = cv2.addWeighted(lane_overlay, 0.7, obstacle_overlay, 0.3, 0)
        elif lane_overlay is not None:
            combined_overlay = lane_overlay
        elif obstacle_overlay is not None:
            combined_overlay = obstacle_overlay
        else:
            combined_overlay = image
        
        # Convert back to base64
        processed_base64 = self.image_to_base64(combined_overlay)
        
        # Combine detection data
        result = {
            'processed_frame': processed_base64,
            'lane_data': lane_data,
            'obstacle_data': obstacle_data,
            'navigation_command': self._generate_navigation_command(lane_data, obstacle_data)
        }
        
        return result
    
    def _generate_navigation_command(self, lane_data: Dict, obstacle_data: Dict) -> Dict:
        """Generate navigation command based on detections"""
        command = {
            'speed': 50,  # Default speed
            'turn': None,  # 'left', 'right', or None
            'led_mode': 0,  # LED mode
            'led_left': False,
            'led_right': False
        }
        
        # Priority 1: Obstacle avoidance
        if obstacle_data.get('should_turn'):
            command['speed'] = 20  # Slow down
            turn_dir = obstacle_data.get('turn_direction')
            command['turn'] = turn_dir
            if turn_dir == 'left':
                command['led_left'] = True
            elif turn_dir == 'right':
                command['led_right'] = True
        
        # Priority 2: Lane centering
        elif lane_data.get('turn_direction'):
            turn_dir = lane_data.get('turn_direction')
            command['turn'] = turn_dir
            command['speed'] = 40  # Moderate speed for lane keeping
            if turn_dir == 'left':
                command['led_left'] = True
            elif turn_dir == 'right':
                command['led_right'] = True
        
        return command


# Singleton instance
processor = AIVideoProcessor()

