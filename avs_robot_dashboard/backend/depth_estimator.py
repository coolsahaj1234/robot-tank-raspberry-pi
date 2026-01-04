"""
Depth Estimation using Apple's Depth Pro Model
Provides accurate metric depth estimation for detected objects.
"""
import numpy as np
import torch
import logging
from PIL import Image
import cv2

logger = logging.getLogger("DepthEstimator")


class DepthProEstimator:
    """
    Wrapper for Apple's Depth Pro model to estimate metric depth from images.
    """

    def __init__(self, device=None):
        """
        Initialize Depth Pro model.

        Args:
            device: 'cuda', 'mps', or 'cpu'. Auto-detects if None.
        """
        self.model = None
        self.transform = None

        # Auto-detect best available device
        if device is None:
            if torch.cuda.is_available():
                device = 'cuda'
            elif torch.backends.mps.is_available():
                device = 'mps'
            else:
                device = 'cpu'

        self.device = device

        try:
            # Import depth_pro package
            from depth_pro import create_model_and_transforms

            # Load model and transforms
            logger.info(f"🔧 Loading Depth Pro model on {device}...")
            self.model, self.transform = create_model_and_transforms(device=device)
            self.model.eval()

            logger.info("✅ Depth Pro model loaded successfully")
            self.enabled = True

        except ImportError:
            logger.warning("⚠️ depth-pro package not installed. Run: pip install depth-pro")
            logger.warning("   Using fallback heuristic depth estimation")
            self.enabled = False

        except Exception as e:
            logger.error(f"❌ Failed to load Depth Pro: {e}")
            logger.warning("   Using fallback heuristic depth estimation")
            self.enabled = False

    def estimate_depth(self, image):
        """
        Estimate depth map from an image.

        Args:
            image: numpy array (H, W, 3) in BGR format (OpenCV)

        Returns:
            depth_map: numpy array (H, W) with metric depth in meters
            focal_length: focal length in pixels (optional)
        """
        if not self.enabled:
            return None, None

        try:
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Convert to PIL Image
            pil_image = Image.fromarray(image_rgb)

            # Apply transforms
            input_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)

            # Run inference
            with torch.no_grad():
                prediction = self.model.infer(input_tensor)

            # Extract depth map
            depth_map = prediction['depth'].squeeze().cpu().numpy()

            # Get focal length if available
            focal_length = prediction.get('focal_length', None)
            if focal_length is not None:
                focal_length = focal_length.item()

            return depth_map, focal_length

        except Exception as e:
            logger.error(f"❌ Depth estimation failed: {e}")
            return None, None

    def get_object_depth(self, depth_map, bbox):
        """
        Get median depth of an object from its bounding box.

        Args:
            depth_map: numpy array (H, W) with depth values in meters
            bbox: [x, y, w, h] bounding box coordinates

        Returns:
            depth: median depth in meters for the object
        """
        if depth_map is None:
            return None

        try:
            x, y, w, h = bbox
            x, y, w, h = int(x), int(y), int(w), int(h)

            # Extract region of interest
            roi = depth_map[y:y+h, x:x+w]

            if roi.size == 0:
                return None

            # Use median depth (robust to outliers)
            depth = np.median(roi)

            return float(depth)

        except Exception as e:
            logger.error(f"❌ Failed to extract object depth: {e}")
            return None

    def get_object_depth_and_position(self, depth_map, bbox, focal_length=None):
        """
        Get 3D position (depth, lateral offset) of an object.

        Args:
            depth_map: numpy array (H, W) with depth values in meters
            bbox: [x, y, w, h] bounding box coordinates
            focal_length: focal length in pixels (optional, for better lateral offset)

        Returns:
            dict with:
                - depth: depth in meters
                - lateral_offset: left/right offset in meters (left=positive, right=negative)
                - vertical_offset: up/down offset in meters (optional)
        """
        if depth_map is None:
            return None

        try:
            x, y, w, h = bbox

            # Get depth at object center
            obj_center_x = int(x + w / 2)
            obj_center_y = int(y + h / 2)

            # Extract ROI for robust depth estimation
            roi = depth_map[max(0, int(y)):min(depth_map.shape[0], int(y+h)),
                           max(0, int(x)):min(depth_map.shape[1], int(x+w))]

            if roi.size == 0:
                return None

            # Median depth for robustness
            depth = np.median(roi)

            # Calculate lateral offset from image center
            img_height, img_width = depth_map.shape
            image_center_x = img_width / 2.0
            image_center_y = img_height / 2.0

            # Pixel offsets from center
            pixel_offset_x = obj_center_x - image_center_x
            pixel_offset_y = obj_center_y - image_center_y

            # Convert to metric offset using depth and focal length
            if focal_length is not None:
                # Use proper pinhole camera model
                lateral_offset = -(pixel_offset_x / focal_length) * depth  # Negate for vehicle coords
                vertical_offset = -(pixel_offset_y / focal_length) * depth
            else:
                # Fallback: assume FOV of 60 degrees (typical webcam)
                fov_rad = 1.047  # 60 degrees
                lateral_offset = -(pixel_offset_x / img_width) * depth * 2.0 * np.tan(fov_rad / 2.0)
                vertical_offset = -(pixel_offset_y / img_height) * depth * 2.0 * np.tan(fov_rad / 2.0)

            return {
                'depth': float(depth),
                'lateral_offset': float(lateral_offset),
                'vertical_offset': float(vertical_offset),
                'confidence': 1.0  # Depth Pro provides high-quality estimates
            }

        except Exception as e:
            logger.error(f"❌ Failed to compute 3D position: {e}")
            return None


class FallbackDepthEstimator:
    """
    Fallback heuristic depth estimation when Depth Pro is not available.
    Uses bounding box size and position (existing approach).
    """

    def __init__(self):
        self.enabled = True
        logger.info("📏 Using fallback heuristic depth estimation")

    def estimate_depth_from_bbox(self, bbox, img_height, img_width):
        """
        Estimate depth using heuristics based on bbox size and position.

        Args:
            bbox: [x, y, w, h]
            img_height, img_width: image dimensions

        Returns:
            dict with depth and lateral_offset
        """
        x, y, w, h = bbox

        # Normalize height and vertical position
        normalized_height = h / img_height
        bbox_bottom_y = (y + h) / img_height  # 0=top, 1=bottom

        # Size-based depth estimate (in meters, not scaled)
        if normalized_height > 0.5:  # Very large (>50% of frame)
            size_depth = 0.15  # 15cm
        elif normalized_height > 0.3:  # Large (30-50%)
            size_depth = 0.25  # 25cm
        elif normalized_height > 0.15:  # Medium (15-30%)
            size_depth = 0.5   # 50cm
        else:  # Small (<15%)
            size_depth = 1.5   # 1.5m

        # Position-based adjustment
        if bbox_bottom_y > 0.7:  # Bottom 30% of frame
            position_factor = 0.6  # Closer
        elif bbox_bottom_y > 0.5:  # Mid-frame
            position_factor = 1.0  # Normal
        else:  # Top of frame
            position_factor = 2.0  # Farther

        estimated_depth = size_depth * position_factor

        # Cap at reasonable range (in meters)
        estimated_depth = min(estimated_depth, 2.0)  # Max 2m
        estimated_depth = max(estimated_depth, 0.05)  # Min 5cm

        # Calculate lateral offset
        bbox_center_x = x + w / 2.0
        image_center_x = img_width / 2.0
        lateral_offset_px = bbox_center_x - image_center_x

        # Convert to meters using depth (assume 60 deg FOV)
        fov_rad = 1.047
        lateral_offset = -(lateral_offset_px / img_width) * estimated_depth * 2.0 * np.tan(fov_rad / 2.0)

        return {
            'depth': float(estimated_depth),
            'lateral_offset': float(lateral_offset),
            'vertical_offset': 0.0,
            'confidence': 0.5  # Lower confidence for heuristic
        }
