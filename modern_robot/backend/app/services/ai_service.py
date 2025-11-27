import asyncio
import cv2
import numpy as np
from app.core.config import settings

class AIService:
    def __init__(self):
        self.is_running = False
        self.model = None
        
        # Load model only if not in mock mode or if requested
        # Using a tiny model for Pi optimization
        if not settings.MOCK_MODE:
            try:
                from ultralytics import YOLO
                self.model = YOLO('yolov8n.pt') 
                print("YOLO model loaded.")
            except ImportError:
                print("Ultralytics not installed. AI features disabled.")
            except Exception as e:
                print(f"Failed to load YOLO model: {e}")

    async def start(self):
        self.is_running = True
        print("AI Service Started")

    async def stop(self):
        self.is_running = False
        print("AI Service Stopped")

    def process_frame(self, frame):
        """
        Run inference on a single frame.
        Returns the annotated frame and a list of detections.
        """
        if self.model is None or frame is None:
            return frame, []

        try:
            results = self.model(frame, stream=True, verbose=False)
            
            detections = []
            annotated_frame = frame.copy()

            for result in results:
                # Plot results on the frame
                annotated_frame = result.plot()
                
                # Extract detection data
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    label = result.names[cls_id]
                    
                    detections.append({
                        "label": label,
                        "confidence": conf,
                        "bbox": box.xyxy[0].tolist()
                    })
            
            return annotated_frame, detections

        except Exception as e:
            print(f"Inference error: {e}")
            return frame, []

    def detect_person(self, frame):
        _, detections = self.process_frame(frame)
        return any(d['label'] == 'person' for d in detections)

    def detect_trash(self, frame):
        # Simply check for common trash items
        trash_labels = ['bottle', 'cup', 'can']
        _, detections = self.process_frame(frame)
        return any(d['label'] in trash_labels for d in detections)
