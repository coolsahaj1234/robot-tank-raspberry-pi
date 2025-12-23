# Servo Jitter Reduction - Implementation Summary

## Problem
Servos were experiencing jittering (unwanted small vibrations/movements) during operation, especially during continuous movement or when receiving frequent update commands.

## Root Causes Identified
1. **Too frequent updates**: Test code was updating servos every 10ms (0.01s) with 1-degree steps
2. **No debouncing**: Every angle change triggered an immediate PWM update, even for micro-movements
3. **No smoothing**: Rapid angle changes caused abrupt PWM signal changes
4. **Software PWM limitations**: Software PWM (gpiozero) is more susceptible to jitter than hardware PWM

## Solutions Implemented

### 1. Debouncing (Time-based throttling)
- **Minimum update interval**: 50ms between servo updates
- **Purpose**: Prevents PWM updates from happening too frequently, allowing the servo to stabilize between commands
- **Implementation**: Tracks last update time per servo channel

### 2. Angle Change Threshold
- **Minimum angle change**: 1.0 degree
- **Purpose**: Ignores micro-movements that don't require actual servo movement
- **Implementation**: Only updates PWM if angle changed by at least 1 degree

### 3. Smoothing Filter (Exponential Moving Average)
- **Smoothing factor**: 0.3 (30% new value, 70% previous smoothed value)
- **Purpose**: Smooths out rapid angle changes, reducing abrupt PWM transitions
- **Implementation**: Applies exponential moving average to angle values before PWM update

### 4. Improved Test Timing
- **Step size**: Changed from 1 degree to 2 degrees
- **Delay**: Increased from 10ms to 80ms between updates
- **Purpose**: Allows debouncing to work effectively and reduces update frequency

## Code Changes

### servo.py
- Added debouncing and smoothing logic to `setServoAngle()` method
- Added tracking variables: `last_servo_angles`, `last_servo_update_time`, `servo_smoothed_angles`
- Added configurable parameters: `servo_min_update_interval`, `servo_min_angle_change`, `servo_smoothing_factor`
- Added `force_update` parameter to bypass debouncing when needed (e.g., on shutdown)

### test.py
- Updated `test_Servo()` function to use 2-degree steps instead of 1-degree
- Increased delay from 10ms to 80ms between updates
- Added informative print statements about jitter reduction

## Configuration Parameters

You can adjust these parameters in `servo.py` if needed:

```python
self.servo_min_update_interval = 0.05  # Minimum time between updates (seconds)
self.servo_min_angle_change = 1.0      # Minimum angle change to trigger update (degrees)
self.servo_smoothing_factor = 0.3      # Smoothing factor (0.0-1.0, lower = more smoothing)
```

### Tuning Guidelines
- **More smoothing** (lower factor, e.g., 0.1-0.2): Reduces jitter but may feel sluggish
- **Less smoothing** (higher factor, e.g., 0.5-0.8): More responsive but may have more jitter
- **Longer interval** (e.g., 0.1s): Better for reducing jitter but slower response
- **Shorter interval** (e.g., 0.03s): Faster response but may have more jitter
- **Larger angle threshold** (e.g., 2-3°): Better for reducing micro-movements but less precise

## Additional Recommendations

### Hardware Solutions (if jitter persists)
1. **Power Supply**: Use a dedicated 5V power supply for servos (not from Raspberry Pi)
2. **Capacitors**: Add a 100-1000µF capacitor across servo power supply
3. **Wiring**: Use short, high-quality wires and twisted-pair cables
4. **Hardware PWM**: Use Raspberry Pi 5 with hardware PWM (already implemented for Pi 5)
5. **Servo Controller**: Consider using a dedicated servo controller board (e.g., Adafruit PWM HAT)

### Software Solutions (already implemented)
- ✅ Debouncing (time-based throttling)
- ✅ Angle change threshold
- ✅ Smoothing filter
- ✅ Proper PWM frequency (50Hz)
- ✅ Frame width configuration (20ms for gpiozero)

## Testing

Run the servo test:
```bash
python3 test.py Servo
```

Expected behavior:
- Servos should move smoothly without jittering
- Movement should be slightly slower but more stable
- No micro-vibrations when servos are stationary

## Notes

- The debouncing and smoothing are automatically applied to all servo commands
- Use `force_update=True` parameter if you need immediate update (e.g., emergency stop)
- The `server_headless.py` already had similar debouncing logic - this implementation makes it consistent across all code

