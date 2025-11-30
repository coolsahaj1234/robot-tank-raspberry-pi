import cv2
import asyncio
import threading
import sys
import time
from typing import Optional, Generator
from app.core.config import settings
import io
import numpy as np

# Try importing picamera2, adding system path if needed
try:
    from picamera2 import Picamera2
    # Also try to import Transform from libcamera
    from libcamera import Transform
    PICAMERA_AVAILABLE = True
except ImportError:
    try:
        sys.path.append('/usr/lib/python3/dist-packages')
        from picamera2 import Picamera2
        from libcamera import Transform
        PICAMERA_AVAILABLE = True
    except ImportError:
        PICAMERA_AVAILABLE = False
        print("Picamera2/libcamera not found. Falling back to OpenCV.")

class CameraStream:
    def __init__(self, camera_id: int):
        self.camera_id = camera_id
        self.cap = None
        self.picam2 = None
        self.is_running = False
        self.frame = None
        self.lock = threading.Lock()
        self.use_picamera = PICAMERA_AVAILABLE and camera_id == 0 # Only use Picamera2 for main camera (usually 0)
        self.zoom_factor = 1.0
        self.base_width = 400
        self.base_height = 300

    def set_zoom(self, factor: float):
        self.zoom_factor = max(1.0, min(factor, 5.0)) # Limit zoom 1x to 5x
        print(f"Camera {self.camera_id} Zoom set to {self.zoom_factor}x")

    def _apply_zoom(self, frame):
        if self.zoom_factor <= 1.01:
            return frame
        
        try:
            h, w = frame.shape[:2]
            new_w = int(w / self.zoom_factor)
            new_h = int(h / self.zoom_factor)
            
            x1 = (w - new_w) // 2
            y1 = (h - new_h) // 2
            x2 = x1 + new_w
            y2 = y1 + new_h
            
            # Crop
            cropped = frame[y1:y2, x1:x2]
            # Resize back to original
            return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)
        except Exception as e:
            print(f"Zoom error: {e}")
            return frame

    def start(self):
        if settings.MOCK_MODE:
            self.is_running = True
            return

        if self.use_picamera:
            try:
                self.picam2 = Picamera2()
                # Use specified resolution and flips
                config = self.picam2.create_preview_configuration(
                    main={"size": (self.base_width, self.base_height)}, 
                    transform=Transform(hflip=1, vflip=1)
                )
                self.picam2.configure(config)
                self.picam2.start()
                self.is_running = True
                print(f"Started Picamera2 for camera {self.camera_id} ({self.base_width}x{self.base_height}, H/V Flip)")
                threading.Thread(target=self._update_picamera, daemon=True).start()
                return
            except Exception as e:
                print(f"Failed to start Picamera2: {e}. Falling back to OpenCV.")
                self.use_picamera = False

        # Fallback or secondary camera
        self.cap = cv2.VideoCapture(self.camera_id)
        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.base_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.base_height)
        
        if not self.cap.isOpened():
            print(f"Failed to open camera {self.camera_id}")
            return

        self.is_running = True
        print(f"Started OpenCV capture for camera {self.camera_id} ({self.base_width}x{self.base_height})")
        threading.Thread(target=self._update_opencv, daemon=True).start()

    def _update_opencv(self):
        while self.is_running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Apply flips for OpenCV (hflip=True, vflip=True means flip code -1)
                frame = cv2.flip(frame, -1)
                frame = self._apply_zoom(frame)
                with self.lock:
                    self.frame = frame
            else:
                time.sleep(0.1)

    def _update_picamera(self):
        while self.is_running:
            try:
                # Picamera2 array capture is efficient
                frame = self.picam2.capture_array()
                # Picamera2 returns RGB, OpenCV expects BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                frame = self._apply_zoom(frame)
                with self.lock:
                    self.frame = frame
            except Exception as e:
                print(f"Picamera2 capture error: {e}")
                time.sleep(0.1)

    def stop(self):
        self.is_running = False
        if self.picam2:
            self.picam2.stop()
            self.picam2.close()
        if self.cap:
            self.cap.release()

    def get_frame(self):
        if settings.MOCK_MODE:
            # Generate mock noise frame
            frame = np.random.randint(0, 255, (300, 400, 3), dtype=np.uint8)
            cv2.putText(frame, f"MOCK CAM {self.camera_id} Z:{self.zoom_factor:.1f}x", (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            ret, buffer = cv2.imencode('.jpg', frame)
            return buffer.tobytes()

        with self.lock:
            if self.frame is None:
                return None
            ret, buffer = cv2.imencode('.jpg', self.frame)
            return buffer.tobytes()

class CameraManager:
    def __init__(self):
        # Front Camera (0), Rear Camera (1)
        self.front_cam = CameraStream(0)
        # self.rear_cam = CameraStream(1) # DISABLED 
    
    def set_zoom(self, camera_type: str, factor: float):
        if camera_type == "front":
            self.front_cam.set_zoom(factor)
        # elif camera_type == "rear":
        #    self.rear_cam.set_zoom(factor)

    def start(self):
        print("Starting cameras...")
        self.front_cam.start()
        # Only start rear cam if it exists (check usb devices?) - keeping simple for now
        # self.rear_cam.start() 

    def stop(self):
        self.front_cam.stop()
        # self.rear_cam.stop()

    def get_stream(self, cam_type: str):
        if cam_type == "front":
            camera = self.front_cam
        else:
            return # No rear camera
            # camera = self.rear_cam
            # # Lazy start for rear camera
            # if not camera.is_running:
            #     camera.start()

        while True:
            frame = camera.get_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                time.sleep(0.1)

    def get_latest_frame(self, cam_type="front"):
        if cam_type == "front":
            with self.front_cam.lock:
                return self.front_cam.frame.copy() if self.front_cam.frame is not None else None
        else:
            return None
            # with self.rear_cam.lock:
            #     return self.rear_cam.frame.copy() if self.rear_cam.frame is not None else None
