# Servo Jitter Fix Guide

## Problem
Severe servo jitter and robot shaking when server is running. This is caused by software PWM (gpiozero) being sensitive to CPU load from video streaming and network I/O.

## Solution 1: Install pigpio (RECOMMENDED - Best Performance)

`pigpio` provides hardware-timed PWM which is much more stable than software PWM. This will eliminate jitter completely.

### Install pigpio from source:

```bash
cd ~
wget https://github.com/joan2937/pigpio/archive/master.zip
unzip master.zip
cd pigpio-master
make
sudo make install
```

### Install Python library:

```bash
sudo pip3 install --break-system-packages pigpio
```

### Start pigpio daemon:

```bash
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

### Verify it's running:

```bash
sudo systemctl status pigpiod
```

The server will automatically detect and use pigpio if available, which will eliminate jitter.

## Solution 2: Current Optimizations (Already Applied)

The code now includes:
1. **Aggressive debouncing**: Only updates servo if angle changed by 3+ degrees OR 150ms passed
2. **PWM stabilization delay**: Small delay after servo updates
3. **Better PWM frame width**: 20ms (50Hz) standard servo frequency

## Solution 3: Reduce CPU Load

If jitter persists, reduce video stream quality:

Edit `server_headless.py` line 28:
```python
self.camera = Camera(stream_size=(320, 240))  # Smaller = less CPU load
```

Or reduce video frame rate by modifying the video thread sleep time.

## Solution 4: Increase Debouncing (If Still Jittery)

Edit `server_headless.py` around line 53-54:
```python
self.servo_min_update_interval = 0.2  # Increase to 200ms
self.servo_min_angle_change = 5  # Increase to 5 degrees
```

## Testing

After installing pigpio, restart the server:
```bash
sudo python server_headless.py
```

You should see: "Info: pigpio not available, using gpiozero for servo control" change to using pigpio automatically.

## Why pigpio is Better

- **Hardware-timed PWM**: Uses dedicated hardware, not CPU cycles
- **No jitter**: Stable PWM signal regardless of CPU load
- **Better performance**: Doesn't compete with video streaming/network I/O
- **Professional grade**: Used in production robotics

## Current Status

The code automatically:
- Tries to use pigpio if available (best)
- Falls back to gpiozero if pigpio not available (current - causes jitter)
- Includes aggressive debouncing to minimize jitter with gpiozero

**Recommendation**: Install pigpio for best results!

