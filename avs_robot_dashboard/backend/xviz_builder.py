import json
import time
import numpy as np

class XVIZBuilder:
    def __init__(self):
        self.start_time = time.time()
        self.frame_count = 0

    def _get_timestamp(self):
        return time.time()

    def build_metadata(self):
        """
        Constructs the XVIZ metadata for the simulation.
        Defines streams for camera, ultrasonic sensors, and object detections.
        """
        return {
            "type": "metadata",
            "version": "2.0.0",
            "streams": {
                "/vehicle/pose": {
                    "category": "pose"
                },
                "/vehicle/acceleration": {
                    "category": "time_series",
                    "scalar_type": "float",
                    "units": "m/s^2"
                },
                "/vehicle/velocity": {
                    "category": "time_series",
                    "scalar_type": "float",
                    "units": "m/s"
                },
                "/camera/front": {
                    "category": "primitive",
                    "primitive_type": "image"
                },
                "/sensors/ultrasonic/front": {
                    "category": "primitive",
                    "primitive_type": "polygon",
                    "coordinate": "VEHICLE_RELATIVE"
                },
                "/sensors/ultrasonic/back": {
                    "category": "primitive",
                    "primitive_type": "polygon",
                    "coordinate": "VEHICLE_RELATIVE"
                },
                "/objects/detected": {
                    "category": "primitive",
                    "primitive_type": "polygon",
                    "coordinate": "VEHICLE_RELATIVE"
                },
                "/decision/navigation": {
                     "category": "time_series",
                     "scalar_type": "string"
                },
                "/debug/ground": {
                    "category": "primitive",
                    "primitive_type": "polygon",
                    "coordinate": "VEHICLE_RELATIVE"
                }
            }
        }

    def build_frame(self, image_base64, front_dist, back_dist, detected_objects, nav_action):
        """
        Constructs a single XVIZ frame update.
        """
        timestamp = self._get_timestamp()
        self.frame_count += 1
        
        frame = {
            "update_type": "INCREMENTAL",
            "updates": [{
                "timestamp": timestamp,
                "poses": {
                    "/vehicle/pose": {
                        "timestamp": timestamp,
                        "map_origin": {"longitude": -122.401202, "latitude": 37.776695, "altitude": 0},
                        "orientation": [0, 0, 0],
                        "position": [0, 0, 0] 
                    },
                    "/vehicle/acceleration": [0, 0, 0],
                    "/vehicle/velocity": [0, 0, 0]
                },
                "primitives": {
                   "/camera/front": {
                       "images": [{
                           "data": image_base64,
                           "format": "JPEG",
                           "width_px": 640,
                           "height_px": 480
                       }]
                   },
                   "/sensors/ultrasonic/front": {
                       "polygons": self._create_ultrasonic_cone(front_dist, "front")
                   },
                   "/sensors/ultrasonic/back": {
                       "polygons": self._create_ultrasonic_cone(back_dist, "back")
                   },
                   "/objects/detected": {
                       "polygons": self._create_object_polygons(detected_objects)
                   },
                   "/debug/ground": {
                       "polygons": [{
                           "vertices": [
                               [-20, -20, 0],
                               [20, -20, 0],
                               [20, 20, 0],
                               [-20, 20, 0]
                           ],
                           "style": { 
                               "stroke_color": [0, 255, 0, 255],
                               "stroke_width": 0.5,
                               "fill_color": [0, 255, 0, 100],
                               "height": 0.1
                           }
                       }],
                       "circles": [{
                           "center": [0, 0, 0.5],
                           "radius": 5,
                           "style": {
                               "fill_color": [0, 0, 255, 200]
                           }
                       }]
                   }
                },
                "time_series": [
                    {
                        "timestamp": timestamp,
                        "streams": {
                            "/decision/navigation": nav_action
                        }
                    }
                ]
            }]
        }
        return frame

    def _create_ultrasonic_cone(self, distance_cm, position):
        """
        Creates a triangle/cone polygon representing the ultrasonic sensor range.
        distance_cm: distance reading in cm
        position: 'front' or 'back'
        """
        # Convert cm to meters for likely XVIZ scale (usually meters)
        dist_m = float(distance_cm) / 100.0
        
        # Max range visual cap
        if dist_m > 3.0: dist_m = 3.0
        
        # Cone width at the end
        width = dist_m * 0.5 
        
        if position == "front":
            # Triangle pointing +X (forward)
            vertices = [
                [0, 0, 0],
                [dist_m, -width/2, 0],
                [dist_m, width/2, 0]
            ]
            color = [0, 255, 0, 100] # Green semi-transparent
            if dist_m < 0.3: color = [255, 0, 0, 150] # Red if close
            
        else: # Back
             # Triangle pointing -X (backward)
            vertices = [
                [0, 0, 0],
                [-dist_m, -width/2, 0],
                [-dist_m, width/2, 0]
            ]
            color = [0, 0, 255, 100] # Blue semi-transparent
            
        return [{
            "vertices": vertices,
            "style": {
                "fill_color": color,
                "height": 0.1
            }
        }]

    def _create_object_polygons(self, objects):
        """
        Converts detected objects (from AI Processor) into 3D polygons.
        Using simple heuristics to map 2D bbox to 3D world space.
        """
        polygons = []
        
        for obj in objects:
            # bbox is [x, y, w, h] in image coordinates
            # We need to map this to 3D relative to car
            # Heuristic: 
            # - Y in image corresponds to X distance (lower in image = closer)
            # - X in image corresponds to Y lateral position
            
            bbox = obj.get('bbox', [0,0,0,0])
            label = obj.get('type', 'OBSTACLE')
            
            # Normalize coordinates (assuming 640x480 standard, but should adjust dynamically if possible)
            # For now using approximate mapping
            
            # Depth estimation (very rough)
            dist_map = {'close': 0.5, 'medium': 1.5, 'far': 3.0}
            dist = dist_map.get(obj.get('distance', 'medium'), 2.0)
            
            # Lateral position
            # Image center is 0, left is positive Y, right is negative Y (standard vehicle coordinates)
            # Actually standard vehicle: X forward, Y left, Z up.
            
            pos = obj.get('position', 'center')
            y_offset = 0
            if pos == 'left': y_offset = 0.5
            elif pos == 'right': y_offset = -0.5
            
            # Create a box at that location
            size = 0.3 # 30cm box
            
            x_center = dist
            y_center = y_offset
            
            vertices = [
                [x_center - size/2, y_center - size/2, 0],
                [x_center + size/2, y_center - size/2, 0],
                [x_center + size/2, y_center + size/2, 0],
                [x_center - size/2, y_center + size/2, 0]
            ]
            
            color = obj.get('color', (200, 200, 200))
            # specific mapping if color is tuple
            if isinstance(color, tuple) or isinstance(color, list):
                 color = list(color) + [200] # Add alpha
            
            polygons.append({
                "vertices": vertices,
                "style": {
                    "fill_color": color,
                    "height": 0.5 # 50cm tall
                },
                "id": str(label)
            })
            
        return polygons
