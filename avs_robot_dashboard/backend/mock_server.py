#!/usr/bin/env python3
"""
Mock XVIZ Server - Sends known-good XVIZ data to test LogViewer rendering.
This helps isolate whether the issue is data format or frontend rendering.
"""
import asyncio
import websockets
import json
import time
import math

class MockXVIZServer:
    def __init__(self):
        self.start_time = time.time()
        self.frame_count = 0
        self.connected_clients = set()

    def build_metadata(self):
        """Build XVIZ 2.0 compliant metadata"""
        return {
            "version": "2.0.0",
            "streams": {
                "/vehicle_pose": {
                    "category": "POSE"
                },
                "/tracklets/objects": {
                    "category": "PRIMITIVE",
                    "primitive_type": "POLYGON",
                    "stream_style": {
                        "fill_color": [200, 0, 70, 128]
                    },
                    "coordinate": "VEHICLE_RELATIVE"
                },
                "/lidar/points": {
                    "category": "PRIMITIVE",
                    "primitive_type": "CIRCLE",
                    "stream_style": {
                        "radius": 0.2,
                        "fill_color": [0, 255, 0, 255]
                    },
                    "coordinate": "VEHICLE_RELATIVE"
                }
            }
        }

    def build_frame(self):
        """Build a single XVIZ state update frame"""
        self.frame_count += 1
        timestamp = self.start_time + (self.frame_count * 0.1)  # 10 FPS

        # Simulate vehicle moving in a circle
        angle = self.frame_count * 0.02
        x = math.cos(angle) * 10
        y = math.sin(angle) * 10
        yaw = angle + math.pi / 2

        # Create some moving objects
        objects = []
        for i in range(3):
            obj_angle = angle + (i * 2 * math.pi / 3)
            obj_x = 5 + math.cos(obj_angle) * 3
            obj_y = math.sin(obj_angle) * 3
            size = 1.0
            objects.append({
                "vertices": [
                    [obj_x - size, obj_y - size, 0],
                    [obj_x + size, obj_y - size, 0],
                    [obj_x + size, obj_y + size, 0],
                    [obj_x - size, obj_y + size, 0]
                ],
                "base": {
                    "object_id": f"obj_{i}",
                    "style": {
                        "fill_color": [200, 0, 70, 128],
                        "height": 1.5
                    }
                }
            })

        # Create lidar-like points in a semicircle
        points = []
        for i in range(20):
            point_angle = (i / 20) * math.pi - math.pi / 2
            dist = 8 + math.sin(self.frame_count * 0.1 + i) * 2
            points.append({
                "center": [
                    math.cos(point_angle) * dist,
                    math.sin(point_angle) * dist,
                    0
                ],
                "radius": 0.2
            })

        return {
            "update_type": "SNAPSHOT",
            "updates": [{
                "timestamp": timestamp,
                "poses": {
                    "/vehicle_pose": {
                        "timestamp": timestamp,
                        "map_origin": {
                            "longitude": -122.4,
                            "latitude": 37.8,
                            "altitude": 0
                        },
                        "position": [x, y, 0],
                        "orientation": [0, 0, yaw]
                    }
                },
                "primitives": {
                    "/tracklets/objects": {
                        "polygons": objects
                    },
                    "/lidar/points": {
                        "circles": points
                    }
                }
            }]
        }

    async def handler(self, websocket, path):
        """Handle WebSocket connections"""
        self.connected_clients.add(websocket)
        print(f"Client connected. Total: {len(self.connected_clients)}")

        try:
            # Send metadata first
            metadata_msg = {
                "type": "xviz/metadata",
                "data": self.build_metadata()
            }
            await websocket.send(json.dumps(metadata_msg))
            print("Sent metadata")

            # Stream frames at ~10 FPS
            while True:
                frame = self.build_frame()
                frame_msg = {
                    "type": "xviz/state_update",
                    "data": frame
                }
                await websocket.send(json.dumps(frame_msg))

                if self.frame_count % 30 == 0:
                    print(f"Sent frame {self.frame_count}")

                await asyncio.sleep(0.1)  # 10 FPS

        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected")
        finally:
            self.connected_clients.discard(websocket)

    async def start(self):
        print("🧪 Mock XVIZ Server starting on ws://0.0.0.0:8081")
        async with websockets.serve(self.handler, "0.0.0.0", 8081):
            print("✅ Mock server ready - open http://localhost:3000")
            await asyncio.Future()  # Run forever

if __name__ == "__main__":
    server = MockXVIZServer()
    asyncio.run(server.start())
