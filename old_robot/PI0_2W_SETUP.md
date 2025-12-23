# Raspberry Pi 0 2W Setup Guide

## Quick Start

The code now automatically uses `gpiozero` (which comes pre-installed) for servo control on Pi 0 2W, so **no additional installation is required**! Just test it:

```bash
cd ~/Server
sudo python test.py servo
```

## What Changed

The code now:
1. **Automatically detects** if `pigpio` is available
2. **Falls back to `gpiozero`** if `pigpio` is not installed
3. **Supports PCB v2 GPIO pins** (12, 13, 19) with both libraries

## Optional: Install pigpio (for better performance)

If you want to use `pigpio` instead of `gpiozero` (optional, but may provide smoother servo control):

### Option 1: Install from source (Recommended)

```bash
cd ~
wget https://github.com/joan2937/pigpio/archive/master.zip
unzip master.zip
cd pigpio-master
make
sudo make install
```

Then install the Python library:
```bash
sudo pip3 install pigpio
```

Start the daemon:
```bash
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

### Option 2: Install via pip (may work on some systems)

```bash
sudo pip3 install pigpio
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

**Note**: If `pigpio` is not available via apt-get (as you experienced), installing from source is the most reliable method.

## Testing

### Test Servos (works with gpiozero by default)
```bash
sudo python test.py servo
```

### Test Motors
```bash
sudo python test.py motor
```

### Test LEDs (requires SPI enabled and packages installed)
First, install required packages using apt (recommended):
```bash
sudo apt-get update
sudo apt-get install python3-numpy python3-spidev
```

**OR** if apt packages are not available, use pip3 with override flag:
```bash
sudo pip3 install --break-system-packages numpy spidev
```

Then enable SPI if not already enabled:
```bash
sudo raspi-config
# Navigate to: Interface Options → SPI → Enable
sudo reboot
```

Then test:
```bash
sudo python test.py led
```

### Test Ultrasonic Sensors
```bash
sudo python test.py ultrasonic
```

### Test Camera (requires picamera2 installed)
First, install picamera2:
```bash
sudo apt-get update
sudo apt-get install python3-picamera2
```

Then test:
```bash
sudo python test.py camera
```

**Note**: Make sure your camera is connected and enabled in raspi-config if needed.

## Troubleshooting

### Servo Not Moving
1. **Make sure you're using `sudo`**: GPIO access requires root privileges
   ```bash
   sudo python test.py servo
   ```

2. **Check which library is being used**: The code will print a message if using gpiozero fallback

3. **Verify wiring**: 
   - Servo 0: GPIO 12
   - Servo 1: GPIO 13  
   - Servo 2: GPIO 19

### If You Want to Force gpiozero
The code automatically uses gpiozero if pigpio is not available. No action needed!

### If You Want to Use pigpio
Follow the installation steps above. The code will automatically detect and use pigpio if available.

## Differences: gpiozero vs pigpio

| Feature | gpiozero | pigpio |
|---------|----------|--------|
| Installation | Pre-installed | Requires installation |
| Performance | Good | Excellent (hardware-timed) |
| Jitter | Slight | Minimal |
| Ease of use | Very easy | Requires daemon |

**For most use cases, gpiozero works perfectly fine!**

## Summary

✅ **No installation required** - gpiozero works out of the box  
✅ **Automatic fallback** - Code handles missing pigpio gracefully  
✅ **PCB v2 supported** - Correct GPIO pins (12, 13, 19)  
✅ **Just test it**: `sudo python test.py servo`

