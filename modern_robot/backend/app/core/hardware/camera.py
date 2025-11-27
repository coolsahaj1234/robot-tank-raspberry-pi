import cv2
import asyncio
import threading
from typing import Optional, Generator
from app.core.config import settings

class CameraStream:
    def __init__(self, camera_id: int):
        self.camera_id = camera_id
        self.cap = None
        self.is_running = False
        self.frame = None
        self.lock = threading.Lock()

    def start(self):
        if settings.MOCK_MODE:
            self.is_running = True
            return

        self.cap = cv2.VideoCapture(self.camera_id)
        # Set common resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        if not self.cap.isOpened():
            print(f"Failed to open camera {self.camera_id}")
            return

        self.is_running = True
        # Start reading thread
        threading.Thread(target=self._update, daemon=True).start()

    def _update(self):
        while self.is_running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame
            else:
                # Reconnection logic could go here
                pass

    def stop(self):
        self.is_running = False
        if self.cap:
            self.cap.release()

    def get_frame(self):
        if settings.MOCK_MODE:
            # Generate mock noise frame
            import numpy as np
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, f"MOCK CAM {self.camera_id}", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            ret, buffer = cv2.imencode('.jpg', frame)
            return buffer.tobytes()

        with self.lock:
            if self.frame is None:
                return None
            ret, buffer = cv2.imencode('.jpg', self.frame)
            return buffer.tobytes()

class CameraManager:
    def __init__(self):
        # Front Camera (0), Rear Camera (1) (Indices might flip depending on connection order)
        self.front_cam = CameraStream(0)
        self.rear_cam = CameraStream(1) # Assuming second camera is index 1

    def start(self):
        print("Starting cameras...")
        self.front_cam.start()
        self.rear_cam.start()

    def stop(self):
        self.front_cam.stop()
        self.rear_cam.stop()

    def get_stream(self, cam_type: str):
        if cam_type == "front":
            camera = self.front_cam
        else:
            camera = self.rear_cam

        while True:
            frame = camera.get_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                # Need a small sleep to prevent tight loop if no frame
                import time
                time.sleep(0.1)

    def get_latest_frame(self, cam_type="front"):
        if cam_type == "front":
            with self.front_cam.lock:
                return self.front_cam.frame.copy() if self.front_cam.frame is not None else None
        else:
            with self.rear_cam.lock:
                return self.rear_cam.frame.copy() if self.rear_cam.frame is not None else None

