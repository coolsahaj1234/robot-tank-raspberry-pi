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
        current_time = time.time()
        return {
            "version": "2.0.0",
            "log_info": {
                "start_time": current_time,
                "end_time": current_time + 86400  # 24 hours
            },
            "streams": {
                "/vehicle_pose": {
                    "category": "POSE"
                },
                "/camera/front": {
                    "category": "PRIMITIVE",
                    "primitive_type": "IMAGE"
                },
                "/vehicle/body": {
                    "category": "PRIMITIVE",
                    "primitive_type": "POLYGON",
                    "coordinate": "VEHICLE_RELATIVE"
                },
                "/sensors/ultrasonic/front": {
                    "category": "PRIMITIVE",
                    "primitive_type": "POLYGON",
                    "coordinate": "VEHICLE_RELATIVE"
                },
                "/sensors/ultrasonic/back": {
                    "category": "PRIMITIVE",
                    "primitive_type": "POLYGON",
                    "coordinate": "VEHICLE_RELATIVE"
                },
                "/objects/detected": {
                    "category": "PRIMITIVE",
                    "primitive_type": "POLYGON",
                    "coordinate": "VEHICLE_RELATIVE"
                },
                "/objects/labels": {
                    "category": "PRIMITIVE",
                    "primitive_type": "TEXT",
                    "coordinate": "VEHICLE_RELATIVE"
                },
                "/ground_plane": {
                    "category": "PRIMITIVE",
                    "primitive_type": "POLYGON",
                    "coordinate": "VEHICLE_RELATIVE"
                }
            }
        }

    def build_frame(self, image_base64, front_dist, back_dist, detected_objects, nav_action, 
                    robot_pose=None, imu_data=None):
        """
        Constructs a single XVIZ frame update.
        
        Args:
            image_base64: Base64 encoded camera frame
            front_dist: Front ultrasonic distance in cm
            back_dist: Back ultrasonic distance in cm
            detected_objects: List of detected objects from AI
            nav_action: Current navigation action/decision
            robot_pose: Dict with 'position', 'orientation', 'velocity' (optional)
            imu_data: Dict with 'accel' and 'gyro' data (optional)
        """
        timestamp = self._get_timestamp()
        self.frame_count += 1
        
        # Default pose if not provided
        if robot_pose is None:
            robot_pose = {
                'position': [0, 0, 0],
                'orientation': [0, 0, 0],
                'velocity': [0, 0, 0]
            }
        
        if imu_data is None:
            imu_data = {
                'accel': {'x': 0, 'y': 0, 'z': 0},
                'gyro': {'x': 0, 'y': 0, 'z': 0}
            }
        
        # Extract pose data - scale up position for visibility (IMU gives small values)
        raw_pos = robot_pose.get('position', [0, 0, 0])
        pos = [raw_pos[0] * 100, raw_pos[1] * 100, raw_pos[2]]  # Scale X,Y by 100x for visibility
        orient = robot_pose.get('orientation', [0, 0, 0])
        vel = robot_pose.get('velocity', [0, 0, 0])
        
        # Extract IMU data
        accel = [
            imu_data.get('accel', {}).get('x', 0),
            imu_data.get('accel', {}).get('y', 0),
            imu_data.get('accel', {}).get('z', 0)
        ]
        
        frame = {
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
                        "position": pos,
                        "orientation": orient
                    }
                },
                "primitives": {
                    "/camera/front": {
                        "images": [{
                            "data": image_base64,
                            "width_px": 640,
                            "height_px": 480
                        }]
                    },
                    "/vehicle/body": {
                        "polygons": self._create_vehicle_body()
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
                    "/objects/labels": {
                        "texts": self._create_object_labels(detected_objects)
                    },
                    "/ground_plane": {
                        "polygons": [{
                            "vertices": [
                                [-10, -10, 0],
                                [10, -10, 0],
                                [10, 10, 0],
                                [-10, 10, 0]
                            ],
                            "base": {
                                "object_id": "ground",
                                "style": {
                                    "fill_color": [40, 40, 40, 200],
                                    "height": 0.01
                                }
                            }
                        }]
                    }
                },
                "variables": {
                    "/sensors/imu": {
                        "accel": {
                            "x": imu_data.get('accel', {}).get('x', 0),
                            "y": imu_data.get('accel', {}).get('y', 0),
                            "z": imu_data.get('accel', {}).get('z', 0)
                        },
                        "gyro": {
                            "x": imu_data.get('gyro', {}).get('x', 0),
                            "y": imu_data.get('gyro', {}).get('y', 0),
                            "z": imu_data.get('gyro', {}).get('z', 0)
                        }
                    }
                }
            }]
        }
        return frame

    def _create_vehicle_body(self):
        """
        Creates a simple arrow-shaped vehicle body.
        Front faces +X direction.
        """
        scale = 10.0

        return [{
            "vertices": [
                [0.2*scale, 0, 0],           # Front point (arrow tip)
                [0.1*scale, 0.1*scale, 0],   # Front-left
                [-0.1*scale, 0.1*scale, 0],  # Back-left
                [-0.1*scale, -0.1*scale, 0], # Back-right
                [0.1*scale, -0.1*scale, 0],  # Front-right
            ],
            "base": {
                "object_id": "vehicle",
                "style": {
                    "fill_color": [70, 130, 180, 200],  # Steel blue
                    "stroke_color": [255, 255, 255, 255],  # White outline
                    "height": 0.5*scale  # 5m tall
                }
            }
        }]

    def _create_ultrasonic_cone(self, distance_cm, position):
        """
        Creates a simple colored bar representing ultrasonic sensor reading.
        distance_cm: distance reading in cm
        position: 'front' or 'back'

        Color coding: RED (close/danger) -> ORANGE (medium) -> GREEN (far/safe)
        """
        import logging
        logger = logging.getLogger("XVIZBuilder")

        original_dist_cm = float(distance_cm)

        # Log every 30 frames
        if self.frame_count % 30 == 0:
            logger.info(f"🔊 Ultrasonic {position}: {original_dist_cm:.1f}cm")

        scale = 10.0  # Match vehicle scaling

        # Color based on distance
        # RED = danger (close), ORANGE = caution, GREEN = safe (far)
        if original_dist_cm < 30:  # < 30cm - DANGER - RED
            color = [255, 0, 0, 255]
            color_name = "RED"
        elif original_dist_cm < 60:  # 30-60cm - CAUTION - ORANGE
            color = [255, 140, 0, 255]
            color_name = "ORANGE"
        else:  # > 60cm - SAFE - GREEN
            color = [0, 255, 0, 255]
            color_name = "GREEN"

        if self.frame_count % 30 == 0:
            logger.info(f"    -> {color_name} bar (dist={original_dist_cm:.0f}cm)")

        # Create simple vertical bar at vehicle edge
        bar_width = 0.15 * scale   # 1.5m wide bar
        bar_height = 0.2 * scale   # 2m tall bar (vehicle height level)

        if position == "front":
            # Bar right at front of vehicle (vehicle front is at 0.2*scale = 2m)
            x_pos = 0.21 * scale
            vertices = [
                # Vertical bar (4 corners) - low height, close to vehicle
                [x_pos, -bar_width/2, 0],
                [x_pos, bar_width/2, 0],
                [x_pos, bar_width/2, bar_height],
                [x_pos, -bar_width/2, bar_height],
            ]
        else:  # Back
            # Bar right at back of vehicle (vehicle back is at -0.15*scale = -1.5m)
            x_pos = -0.16 * scale
            vertices = [
                # Vertical bar (4 corners) - low height, close to vehicle
                [x_pos, -bar_width/2, 0],
                [x_pos, bar_width/2, 0],
                [x_pos, bar_width/2, bar_height],
                [x_pos, -bar_width/2, bar_height],
            ]

        return [{
            "vertices": vertices,
            "base": {
                "object_id": f"ultrasonic_{position}",
                "style": {
                    "fill_color": color,
                    "stroke_color": color,
                    "height": 0.1  # Flat bar, not extruded
                }
            }
        }]

    def _create_object_polygons(self, objects):
        """
        Converts detected objects (from AI Processor) into 3D polygons.
        Uses real depth data from Depth Pro or fallback heuristic estimation.

        Vehicle coordinate system: X=forward, Y=left, Z=up
        """
        polygons = []
        scale = 10.0  # Match vehicle and sensor scaling

        for obj in objects:
            bbox = obj.get('bbox', [0, 0, 0, 0])
            label = obj.get('type', 'OBSTACLE')
            confidence = obj.get('confidence', 0.5)
            position_3d = obj.get('position_3d', None)  # Real 3D position from Depth Pro

            import logging
            logger = logging.getLogger("XVIZBuilder")

            # Use real 3D position data if available
            if position_3d and 'depth' in position_3d and 'lateral_offset' in position_3d:
                # Real depth from Depth Pro or improved estimation
                estimated_depth = position_3d['depth'] * scale  # Convert to scaled coordinates
                lateral_offset_m = position_3d['lateral_offset'] * scale

                x, y, w, h = bbox[0], bbox[1], bbox[2], bbox[3]
                logger.info(f"🎯 '{label}': depth={estimated_depth/scale:.2f}m, lateral={lateral_offset_m/scale:.2f}m, bbox=[{x},{y},{w},{h}]")

                # Calculate real-world object size from bbox and depth
                # Assume 60 degree FOV (typical webcam)
                import numpy as np
                fov_rad = 1.047  # 60 degrees
                img_width = 640  # Standard resolution
                img_height = 480

                # Calculate real-world width and height using depth
                # Angular size per pixel at given depth
                pixel_to_meter_x = (2.0 * estimated_depth / scale * np.tan(fov_rad / 2.0)) / img_width
                pixel_to_meter_y = (2.0 * estimated_depth / scale * np.tan(fov_rad / 2.0)) / img_height

                # Convert bbox pixel dimensions to real-world meters, then scale
                obj_width = w * pixel_to_meter_x * scale
                obj_height = h * pixel_to_meter_y * scale

                # Use smaller dimension for the floor footprint (width/depth of object)
                obj_size = min(obj_width, obj_height)
                # Clamp to reasonable sizes (allow smaller objects)
                obj_size = max(0.1 * scale, min(obj_size, 2.0 * scale))  # 10cm to 2m
                obj_height = max(0.1 * scale, min(obj_height, 3.0 * scale))  # 10cm to 3m

                if self.frame_count % 30 == 0:  # Log every 30 frames
                    logger.info(f"   → Calculated size: width={obj_width/scale:.2f}m, height={obj_height/scale:.2f}m, footprint={obj_size/scale:.2f}m")

            else:
                # Fallback: no 3D position data - use legacy distance estimation
                logger.warning(f"⚠️ No 3D data for '{label}', using fallback")
                dist_map = {'close': 0.5*scale, 'medium': 1.5*scale, 'far': 3.0*scale}
                estimated_depth = dist_map.get(obj.get('distance', 'medium'), 2.0*scale)

                pos = obj.get('position', 'center')
                lateral_offset_m = 0
                if pos == 'left':
                    lateral_offset_m = 0.5 * scale
                elif pos == 'right':
                    lateral_offset_m = -0.5 * scale

                # Use bbox dimensions for fallback sizing
                x, y, w, h = bbox[0], bbox[1], bbox[2], bbox[3]
                obj_size = (w / 640.0) * 1.0 * scale  # Rough estimate
                obj_height = (h / 480.0) * 1.5 * scale
            
            # Create 3D bounding box - single polygon with extrusion
            x_center = estimated_depth
            y_center = lateral_offset_m

            # Define base footprint on the ground (Z=0)
            half_size = obj_size / 2

            # Color coding by object type and confidence
            color_map = {
                'person': [255, 100, 100],  # Reddish
                'santa hat': [255, 0, 0],    # Bright red
                'furniture': [100, 100, 255], # Blueish
                'vase': [150, 100, 200],     # Purple
                'potted plant': [100, 200, 100],  # Green
                'OBSTACLE': [200, 200, 200]  # Gray
            }
            base_color = color_map.get(label.lower(), [200, 200, 200])

            # Adjust alpha based on confidence
            alpha = int(150 + confidence * 105)  # 150-255
            color = list(base_color) + [alpha]

            # Create single polygon at ground level that will be extruded upward
            polygons.append({
                "vertices": [
                    [x_center - half_size, y_center - half_size, 0],
                    [x_center + half_size, y_center - half_size, 0],
                    [x_center + half_size, y_center + half_size, 0],
                    [x_center - half_size, y_center + half_size, 0]
                ],
                "base": {
                    "object_id": f"{label}_{self.frame_count}_{len(polygons)}",
                    "style": {
                        "fill_color": color,
                        "stroke_color": base_color + [255],
                        "height": obj_height,  # Extrude upward from ground
                        "extruded": True
                    }
                }
            })
            
        return polygons

    def _create_object_labels(self, objects):
        """
        Creates text labels for detected objects positioned above them in 3D space.
        """
        texts = []
        scale = 10.0  # Match vehicle and sensor scaling

        for obj in objects:
            bbox = obj.get('bbox', [0, 0, 0, 0])
            label = obj.get('type', 'OBSTACLE')
            confidence = obj.get('confidence', 0.5)

            if len(bbox) >= 4:
                x, y, w, h = bbox[0], bbox[1], bbox[2], bbox[3]

                # Use same depth estimation logic as polygons
                img_height = 480
                img_width = 640

                normalized_height = h / img_height
                bbox_bottom_y = (y + h) / img_height

                # Size-based estimate
                if normalized_height > 0.5:
                    size_depth = 0.15
                elif normalized_height > 0.3:
                    size_depth = 0.25
                elif normalized_height > 0.15:
                    size_depth = 0.5
                else:
                    size_depth = 1.5

                # Position-based adjustment
                if bbox_bottom_y > 0.7:
                    position_factor = 0.6
                elif bbox_bottom_y > 0.5:
                    position_factor = 1.0
                else:
                    position_factor = 2.0

                estimated_depth = size_depth * position_factor * scale
                estimated_depth = min(estimated_depth, 2.0 * scale)
                estimated_depth = max(estimated_depth, 0.05 * scale)

                # Lateral offset (negate for vehicle coordinates)
                bbox_center_x = x + w / 2.0
                image_center_x = img_width / 2.0
                lateral_offset_px = bbox_center_x - image_center_x
                fov_rad = 1.047
                lateral_offset_m = -(lateral_offset_px / img_width) * estimated_depth * 2.0 * np.tan(fov_rad / 2.0)

                # Object height for label positioning
                object_heights = {
                    'person': 1.7 * scale,
                    'santa hat': 0.3 * scale,
                    'furniture': 0.8 * scale,
                    'OBSTACLE': 0.5 * scale
                }
                obj_height = object_heights.get(label.lower(), 0.5 * scale)

                # Position label above the object
                # X = forward (depth), Y = lateral (left/right), Z = up (height + offset)
                label_z = obj_height + 0.2 * scale  # 2m above object

                # Format label text with confidence
                label_text = f"{label}\n{confidence:.0%}"

                texts.append({
                    "position": [estimated_depth, lateral_offset_m, label_z],
                    "text": label_text,
                    "style": {
                        "fill_color": [255, 255, 255, 255],  # White text
                        "font_size": 14
                    }
                })
            else:
                # Fallback positioning if bbox not available
                dist_map = {'close': 0.5*scale, 'medium': 1.5*scale, 'far': 3.0*scale}
                estimated_depth = dist_map.get(obj.get('distance', 'medium'), 2.0*scale)

                pos = obj.get('position', 'center')
                lateral_offset_m = 0
                if pos == 'left':
                    lateral_offset_m = 0.5 * scale
                elif pos == 'right':
                    lateral_offset_m = -0.5 * scale

                label_text = f"{label}\n{confidence:.0%}"
                texts.append({
                    "position": [estimated_depth, lateral_offset_m, 0.5 * scale],
                    "text": label_text,
                    "style": {
                        "fill_color": [255, 255, 255, 255],
                        "font_size": 14
                    }
                })

        return texts
