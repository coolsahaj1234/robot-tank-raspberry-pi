#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import cv2
import numpy as np
import base64
import socket
from xviz_builder import XVIZBuilder
from ai_processor import AIVideoProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AVSBackend")

# Robot Connection Settings
ROBOT_IP = '10.0.0.86' # TODO: Make configurable
COMMAND_PORT = 5003
VIDEO_PORT = 8003

class AVSBackendServer:
    def __init__(self):
        self.xviz_builder = XVIZBuilder()
        self.ai_processor = AIVideoProcessor()
        self.connected_clients = set()
        self.robot_video_socket = None
        self.robot_command_socket = None
        
        # State
        self.latest_frame = None
        self.latest_front_dist = 100  # cm
        self.latest_back_dist = 100    # cm
        self.latest_nav_action = 'stop'
        self.detected_objects = []

        # Command writer for sending commands to robot
        self.command_writer = None
        self.current_mode = 0  # 0=stop, 1=manual, 2=sonar, etc.
        
        # IMU State (for pose tracking)
        self.imu_data = {
            'accel': {'x': 0, 'y': 0, 'z': 0},
            'gyro': {'x': 0, 'y': 0, 'z': 0}
        }
        self.robot_pose = {
            'position': [0, 0, 0],  # x, y, z in meters
            'orientation': [0, 0, 0],  # roll, pitch, yaw in radians
            'velocity': [0, 0, 0]  # m/s
        }

    async def connect_to_robot_command(self):
        """Connects to the robot's command port to receive sensor data"""
        while True:  # Retry loop
            try:
                reader, writer = await asyncio.open_connection(ROBOT_IP, COMMAND_PORT)
                self.command_writer = writer  # Store for sending commands
                logger.info(f"✅ Connected to Robot Command at {ROBOT_IP}:{COMMAND_PORT}")

                # Send a dummy command to keep connection alive (robot expects commands)
                writer.write(b'CMD_STATUS\n')
                await writer.drain()
                
                buffer = b''
                while True:
                    data = await reader.read(1024)
                    if not data:
                        break
                        
                    buffer += data
                    
                    # Process complete lines
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        if line:
                            await self.parse_sensor_message(line.decode('utf-8', errors='ignore'))
                                
            except Exception as e:
                logger.error(f"❌ Failed to connect to robot command port: {e}")
                await asyncio.sleep(5)  # Retry delay

    async def parse_sensor_message(self, message):
        """Parses sensor messages from robot (CMD_SONIC, CMD_IMU)"""
        try:
            if message.startswith('CMD_SONIC#'):
                # Format: CMD_SONIC#{front}#{back}\n
                parts = message.strip().split('#')
                if len(parts) == 3:
                    old_front = self.latest_front_dist
                    self.latest_front_dist = float(parts[1])
                    self.latest_back_dist = float(parts[2])
                    # Log when values change significantly
                    if abs(self.latest_front_dist - old_front) > 5:
                        logger.info(f"📡 Sensor: Front={self.latest_front_dist:.1f}cm, Back={self.latest_back_dist:.1f}cm")
                    
            elif message.startswith('CMD_IMU#'):
                # Format: CMD_IMU#{accel_x}#{accel_y}#{accel_z}#{gyro_x}#{gyro_y}#{gyro_z}\n
                parts = message.strip().split('#')
                if len(parts) == 7:
                    self.imu_data = {
                        'accel': {
                            'x': float(parts[1]),
                            'y': float(parts[2]),
                            'z': float(parts[3])
                        },
                        'gyro': {
                            'x': float(parts[4]),
                            'y': float(parts[5]),
                            'z': float(parts[6])
                        }
                    }
                    # Update pose based on IMU (simple integration)
                    self.update_pose_from_imu()
                    logger.debug(f"IMU: Accel=({self.imu_data['accel']['x']:.2f}, {self.imu_data['accel']['y']:.2f}, {self.imu_data['accel']['z']:.2f})")
        except Exception as e:
            logger.warning(f"Failed to parse sensor message '{message}': {e}")

    def update_pose_from_imu(self):
        """Updates robot pose based on IMU data (simplified integration)"""
        # Simple integration - in production, use proper sensor fusion (Kalman filter)
        dt = 0.1  # Approximate time step (sensor updates ~10Hz)
        
        # Update velocity from acceleration (simplified)
        self.robot_pose['velocity'][0] += self.imu_data['accel']['x'] * dt
        self.robot_pose['velocity'][1] += self.imu_data['accel']['y'] * dt
        
        # Update position from velocity
        self.robot_pose['position'][0] += self.robot_pose['velocity'][0] * dt
        self.robot_pose['position'][1] += self.robot_pose['velocity'][1] * dt
        
        # Update orientation from gyro (simplified - only yaw for ground robot)
        self.robot_pose['orientation'][2] += self.imu_data['gyro']['z'] * dt
        
        # Damping to prevent drift
        self.robot_pose['velocity'][0] *= 0.95
        self.robot_pose['velocity'][1] *= 0.95

    async def connect_to_robot_video(self):
        """Connects to the robot's TCP video stream"""
        while True:  # Retry loop
            try:
                reader, writer = await asyncio.open_connection(ROBOT_IP, VIDEO_PORT)
                logger.info(f"✅ Connected to Robot Video at {ROBOT_IP}:{VIDEO_PORT}")
                
                # Read loop
                buffer = b''
                expected_length = None
                
                while True:
                    data = await reader.read(4096)
                    if not data:
                        break
                        
                    buffer += data
                    
                    while True:
                        if expected_length is None:
                            if len(buffer) >= 4:
                                expected_length = int.from_bytes(buffer[:4], byteorder='little')
                                buffer = buffer[4:]
                            else:
                                break
                                
                        if expected_length is not None:
                            if len(buffer) >= expected_length:
                                frame_data = buffer[:expected_length]
                                buffer = buffer[expected_length:]
                                expected_length = None
                                
                                await self.process_robot_frame(frame_data)
                            else:
                                break
                                
            except Exception as e:
                logger.error(f"❌ Failed to connect to robot video: {e}")
                await asyncio.sleep(5)  # Retry delay

    async def process_robot_frame(self, frame_data):
        """Decodes frame, runs AI, and broadcasts XVIZ"""
        try:
            # 1. Decode Image
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                return

            # 1.5. Resize frame to 640x480 for better object detection
            # Use INTER_LINEAR for upscaling (good quality/speed balance)
            h, w = frame.shape[:2]
            if w != 640 or h != 480:
                frame = cv2.resize(frame, (640, 480), interpolation=cv2.INTER_LINEAR)

            # 2. Run AI Processing only every 5th frame to reduce CPU load
            if self.xviz_builder.frame_count % 5 == 0:
                objects = self.ai_processor.detect_objects(frame)
                if len(objects) > 0 and len(objects) != len(self.detected_objects):
                    logger.info(f"🔍 Detected {len(objects)} objects: {[obj.get('type', 'UNKNOWN') for obj in objects]}")
                self.detected_objects = objects

            # 2.5. Draw bounding boxes and labels on frame for visualization
            frame_with_boxes = self._draw_detections(frame, self.detected_objects)

            # Base64 encode for XVIZ (reduce quality for speed)
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, 70]
            _, buffer = cv2.imencode('.jpg', frame_with_boxes, encode_params)
            b64_frame = base64.b64encode(buffer).decode('utf-8')
            
            # 3. Build XVIZ Update with real sensor data
            xviz_frame = self.xviz_builder.build_frame(
                b64_frame,
                self.latest_front_dist,
                self.latest_back_dist,
                self.detected_objects,
                self.latest_nav_action,
                self.robot_pose,
                self.imu_data
            )
            
            # 4. Broadcast - wrap in XVIZ envelope
            xviz_message = {
                "type": "xviz/state_update",
                "data": xviz_frame
            }
            json_msg = json.dumps(xviz_message)
            await self.broadcast(json_msg)

            # 5. Also broadcast sensor state every 10 frames for UI updates
            if self.xviz_builder.frame_count % 10 == 0:
                sensor_msg = json.dumps({
                    "type": "robot/state",
                    "data": {
                        "connected": self.command_writer is not None,
                        "mode": self.current_mode,
                        "sensors": {
                            "front_distance": self.latest_front_dist,
                            "back_distance": self.latest_back_dist,
                            "imu": self.imu_data
                        }
                    }
                })
                await self.broadcast(sensor_msg)
            
            if self.xviz_builder.frame_count % 30 == 0:
                logger.info(f"Broadcasted frame #{self.xviz_builder.frame_count} ({len(json_msg)} bytes)")
                logger.info(f"🚗 Pose: pos={self.robot_pose['position']}, orient={self.robot_pose['orientation']}")
             
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            import traceback
            traceback.print_exc()

    def _draw_detections(self, frame, detected_objects):
        """Draw bounding boxes and labels on frame for validation"""
        overlay = frame.copy()

        for obj in detected_objects:
            bbox = obj.get('bbox', [0, 0, 0, 0])
            if len(bbox) >= 4:
                x, y, w, h = bbox[0], bbox[1], bbox[2], bbox[3]
                label = obj.get('type', 'UNKNOWN')
                confidence = obj.get('confidence', 0.0)

                # Color based on object type
                color_map = {
                    'person': (0, 255, 0),      # Green
                    'boat': (0, 255, 255),      # Yellow
                    'bowl': (255, 128, 0),      # Orange
                    'cup': (255, 128, 0),       # Orange
                    'bottle': (128, 0, 255),    # Purple
                }
                color = color_map.get(label.lower(), (0, 255, 255))  # Default yellow

                # Draw bounding box
                cv2.rectangle(overlay, (x, y), (x + w, y + h), color, 2)

                # Draw label background
                label_text = f"{label} {confidence:.0%}"
                (text_w, text_h), baseline = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(overlay, (x, y - text_h - 10), (x + text_w + 10, y), color, -1)

                # Draw label text
                cv2.putText(overlay, label_text, (x + 5, y - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

                # Draw center crosshair
                center_x = x + w // 2
                center_y = y + h // 2
                cv2.circle(overlay, (center_x, center_y), 3, color, -1)
                cv2.line(overlay, (center_x - 10, center_y), (center_x + 10, center_y), color, 1)
                cv2.line(overlay, (center_x, center_y - 10), (center_x, center_y + 10), color, 1)

        # Draw image center line for reference
        h, w = overlay.shape[:2]
        cv2.line(overlay, (w // 2, 0), (w // 2, h), (128, 128, 128), 1)
        cv2.putText(overlay, "CENTER", (w // 2 - 30, 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 128, 128), 1)

        return overlay

    async def send_robot_command(self, command):
        """Sends a command to the robot"""
        if self.command_writer:
            try:
                self.command_writer.write(f"{command}\n".encode())
                await self.command_writer.drain()
                logger.debug(f"Sent command: {command}")
                return True
            except Exception as e:
                logger.error(f"Failed to send command: {e}")
                return False
        return False

    async def handler(self, websocket, path):
        """WebSocket handler for XVIZ clients"""
        self.connected_clients.add(websocket)
        logger.info("Client connected")

        try:
            # Send Metadata immediately
            metadata = self.xviz_builder.build_metadata()
            await websocket.send(json.dumps({
                "type": "xviz/metadata",
                "data": metadata
            }))

            # Also send current state
            await websocket.send(json.dumps({
                "type": "robot/state",
                "data": {
                    "connected": self.command_writer is not None,
                    "mode": self.current_mode,
                    "sensors": {
                        "front_distance": self.latest_front_dist,
                        "back_distance": self.latest_back_dist,
                        "imu": self.imu_data
                    }
                }
            }))

            async for message in websocket:
                try:
                    msg = json.loads(message)
                    msg_type = msg.get("type", "")

                    if msg_type == "robot/command":
                        # Forward command to robot
                        command = msg.get("command", "")
                        logger.info(f"📨 Received command from client: {command}")
                        if command:
                            success = await self.send_robot_command(command)
                            logger.info(f"📤 Command sent to robot: {command}, success: {success}")
                            # Track mode changes
                            if command.startswith("CMD_MODE#"):
                                self.current_mode = int(command.split("#")[1])
                            await websocket.send(json.dumps({
                                "type": "robot/command_response",
                                "success": success,
                                "command": command
                            }))

                    elif msg_type == "robot/get_state":
                        # Send current state
                        await websocket.send(json.dumps({
                            "type": "robot/state",
                            "data": {
                                "connected": self.command_writer is not None,
                                "mode": self.current_mode,
                                "sensors": {
                                    "front_distance": self.latest_front_dist,
                                    "back_distance": self.latest_back_dist,
                                    "imu": self.imu_data
                                }
                            }
                        }))

                except json.JSONDecodeError:
                    pass  # Ignore non-JSON messages

        finally:
            self.connected_clients.remove(websocket)
            logger.info("Client disconnected")

    async def broadcast(self, message):
        if not self.connected_clients:
            return
        await asyncio.gather(
            *[client.send(message) for client in self.connected_clients],
            return_exceptions=True
        )

    async def start(self):
        # Start WebSocket Server
        async with websockets.serve(self.handler, "0.0.0.0", 8081):
            logger.info("🚀 XVIZ Server running on ws://0.0.0.0:8081")
            
            # Start Robot Connections (both video and command) in parallel
            video_task = asyncio.create_task(self.connect_to_robot_video())
            command_task = asyncio.create_task(self.connect_to_robot_command())
            
            # Wait for both tasks (they will retry on failure)
            await asyncio.gather(video_task, command_task, return_exceptions=True)

if __name__ == "__main__":
    server = AVSBackendServer()
    asyncio.run(server.start())
