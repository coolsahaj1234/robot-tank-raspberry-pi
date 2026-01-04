# Depth Pro & Improved Object Detection Setup

This guide explains how to set up the improved object detection and depth estimation system.

## What's New

The system has been upgraded with:

1. **Better Object Detection**: Upgraded from YOLOv8n (nano) to YOLOv11/YOLOv8x (medium/extra-large) for better accuracy
2. **Apple Depth Pro Integration**: Real metric depth estimation using Apple's Depth Pro model
3. **Accurate 3D Positioning**: Objects in the AVS 3D map now have precise depth and position

## Installation Steps

### 1. Install Depth Pro (Optional but Recommended)

```bash
# Install depth-pro package
pip install depth-pro

# Or install from source for latest version
pip install git+https://github.com/apple/ml-depth-pro.git
```

**Note**: Depth Pro works best with:
- **macOS**: Uses Metal Performance Shaders (MPS) for GPU acceleration
- **CUDA GPUs**: Uses CUDA for GPU acceleration
- **CPU**: Falls back to CPU (slower but works)

### 2. Upgrade YOLO Model

The system will automatically try to download better YOLO models in this order:
1. `yolo11m.pt` (YOLO v11 medium - best balance)
2. `yolov8x.pt` (YOLO v8 extra-large - good accuracy)
3. `yolov8m.pt` (YOLO v8 medium - fallback)
4. `yolov8n.pt` (YOLO v8 nano - last resort)

Models are downloaded automatically by ultralytics when first used.

To manually download a specific model:
```bash
# Python
from ultralytics import YOLO
model = YOLO('yolo11m.pt')  # Downloads yolo11m.pt
```

### 3. Verify Installation

```bash
cd /Users/sandeepsingh/Documents/robot-tank-raspberry-pi-1/avs_robot_dashboard/backend
python3 -c "from depth_estimator import DepthProEstimator; d = DepthProEstimator(); print('✅ Depth Pro ready!' if d.enabled else '⚠️ Using fallback')"
```

## How It Works

### With Depth Pro (Recommended)

1. **Depth Estimation**: For each camera frame, Depth Pro estimates a full depth map
2. **Object Detection**: YOLO detects objects with bounding boxes
3. **3D Position**: For each detected object, we extract its depth from the depth map
4. **Accurate Placement**: Objects appear in the AVS 3D map at their real-world positions

**Advantages**:
- Metric depth (accurate distances in meters)
- Handles complex scenes with multiple objects
- Works at any distance (near and far)
- Better lateral offset calculation

### Without Depth Pro (Fallback)

If Depth Pro is not available, the system uses improved heuristic estimation:
- Estimates depth based on bounding box size and vertical position
- Still provides reasonable 3D visualization
- Faster but less accurate than Depth Pro

## Performance Considerations

### Model Sizes & Speed

| Model | Size | Accuracy | Speed (CPU) | Speed (GPU) |
|-------|------|----------|-------------|-------------|
| YOLOv11m | ~50MB | ⭐⭐⭐⭐⭐ | Medium | Fast |
| YOLOv8x | ~130MB | ⭐⭐⭐⭐ | Slow | Fast |
| YOLOv8m | ~50MB | ⭐⭐⭐ | Medium | Fast |
| YOLOv8n | ~6MB | ⭐⭐ | Fast | Very Fast |

### Depth Pro Performance

- **GPU (MPS/CUDA)**: ~200-500ms per frame
- **CPU**: ~2-5 seconds per frame

For real-time performance, a GPU is highly recommended.

### Optimization Tips

1. **Use GPU**: Depth Pro is much faster with GPU acceleration
2. **Reduce Resolution**: Process smaller images for faster depth estimation
3. **Skip Frames**: Only estimate depth every N frames if needed
4. **Use Medium Models**: YOLOv11m or YOLOv8m provide good balance

## Troubleshooting

### "depth-pro package not installed"

```bash
pip install depth-pro
```

### "No YOLO model could be loaded"

Check your internet connection and try manually downloading:
```bash
python3 -c "from ultralytics import YOLO; YOLO('yolo11m.pt')"
```

### Depth estimation is slow

- Use a GPU if available (MPS on Mac, CUDA on Linux/Windows)
- Consider processing at lower resolution
- Or disable Depth Pro and use fallback (still accurate)

### Objects appear at wrong depths

- Verify Depth Pro is loaded: Check logs for "✅ Depth Pro model loaded"
- Check for depth map range in logs
- Ensure lighting is adequate (depth estimation works best with good lighting)

## Configuration

### Force Fallback Mode

To disable Depth Pro and use only heuristic estimation:

Edit `ai_processor.py` line ~150:
```python
# Force fallback
self.depth_estimator = FallbackDepthEstimator()
```

### Adjust Depth Processing

Edit `depth_estimator.py` to tune:
- Median vs mean depth calculation
- ROI extraction method
- Confidence scores

## Monitoring

Watch the logs for depth information:

```
📏 Depth map estimated: shape=(480, 640), range=[0.25, 5.43]m
🎯 'CAR': depth=1.23m, lateral=-0.45m (Depth Pro)
```

- ✅ "Depth Pro" = using real depth
- ⚠️ "Using fallback" = heuristic estimation

## Next Steps

1. Test the system and observe object positioning in AVS 3D map
2. Adjust YOLO confidence thresholds if needed (in `ai_processor.py`)
3. Fine-tune depth estimation if objects appear too close/far

## References

- [Apple Depth Pro GitHub](https://github.com/apple/ml-depth-pro)
- [Ultralytics YOLOv11 Docs](https://docs.ultralytics.com/)
- [XVIZ Protocol Spec](https://github.com/uber/xviz)
