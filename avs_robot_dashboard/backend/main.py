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
        self.latest_front_dist = 100
        self.latest_back_dist = 100
        self.latest_nav_action = 'stop'
        self.detected_objects = []

    async def connect_to_robot(self):
        """Connects to the robot's TCP video stream"""
        try:
            reader, writer = await asyncio.open_connection(ROBOT_IP, VIDEO_PORT)
            logger.info(f"✅ Connected to Robot Video at {ROBOT_IP}:{VIDEO_PORT}")
            
            # TODO: Also connect to command port if we want to send commands
            # For now, we are just visualizing
            
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
            logger.error(f"❌ Failed to connect to robot: {e}")
            await asyncio.sleep(5) # Retry delay

    async def process_robot_frame(self, frame_data):
        """Decodes frame, runs AI, and broadcasts XVIZ"""
        try:
            # 1. Decode Image
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return

            # 2. Run AI Processing
            # Note: We need ultrasonic data. 
            # In a real scenario, we'd need to parse that from the robot stream or have a separate data stream.
            # For this prototype, we will simulate/extract if possible, or just use what we have.
            # The current robot implementation sends VIDEO only on video port. 
            # We need to bridge the Node.js approach or parse the side-channel data.
            # For now, we will run object detection on the frame.
            
            # Mock sensor data for now since raw video stream doesn't have it embedded usually
            # unless we modify the robot server.
            # TODO: Integrate sensor data stream properly.
            
            # Run detection
            objects = self.ai_processor.detect_objects(frame)
            self.detected_objects = objects
            
            # Base64 encode for XVIZ
            _, buffer = cv2.imencode('.jpg', frame)
            b64_frame = base64.b64encode(buffer).decode('utf-8')
            
            # 3. Build XVIZ Update
            xviz_frame = self.xviz_builder.build_frame(
                b64_frame,
                self.latest_front_dist,
                self.latest_back_dist,
                self.detected_objects,
                self.latest_nav_action
            )
            
            # 4. Broadcast - wrap in XVIZ envelope
            xviz_message = {
                "type": "xviz/state_update",
                "data": xviz_frame
            }
            json_msg = json.dumps(xviz_message)
            await self.broadcast(json_msg)
            
            if self.xviz_builder.frame_count % 30 == 0:
                logger.info(f"Broadcasted frame #{self.xviz_builder.frame_count} ({len(json_msg)} bytes)")
             
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            import traceback
            traceback.print_exc()

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
            
            async for message in websocket:
                pass # keep connection open
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
            
            # Start Robot Connection Loop
            while True:
                await self.connect_to_robot()
                await asyncio.sleep(1)

if __name__ == "__main__":
    server = AVSBackendServer()
    asyncio.run(server.start())
