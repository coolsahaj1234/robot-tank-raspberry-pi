# Servo 2 Testing Guide

## Problem
Servo 2 (channel 2) on GPIO 25 is not working in the test scripts.

## Your Configuration
- **PCB Version**: 2
- **Raspberry Pi**: 5
- **Servo 2 Pin**: GPIO 25 (Software PWM via gpiozero)

## Testing Options

### Option 1: Simple Test (gpiozero - already available)
```bash
cd /home/pi5/Documents/Robot_Kit_for_Raspberry_Pi-main/Code/Server
python3 test_servo2.py
```

This uses the gpiozero library which is already installed. It may have some jitter but should work.

### Option 2: Diagnostic Test
```bash
cd /home/pi5/Documents/Robot_Kit_for_Raspberry_Pi-main/Code/Server
python3 diagnose_servo.py
```

This runs a comprehensive diagnostic and tests servo 2 through multiple positions.

### Option 3: Better PWM Control (pigpio - recommended)
First, install and start pigpio:
```bash
sudo apt-get install -y pigpio python3-pigpio
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

Then run the test:
```bash
cd /home/pi5/Documents/Robot_Kit_for_Raspberry_Pi-main/Code/Server
python3 test_servo2_pigpio.py
```

This provides the most reliable servo control with minimal jitter.

## Troubleshooting Checklist

### 1. Hardware Connections
- [ ] Servo signal wire connected to GPIO 25
- [ ] Servo power (red) connected to 5V power supply
- [ ] Servo ground (black/brown) connected to ground
- [ ] Ground shared between Pi and servo power supply

### 2. Servo Type
- [ ] Verify it's a standard servo (0-180°), not a continuous rotation servo
- [ ] If it IS a continuous rotation servo, angles control speed/direction instead

### 3. Power Supply
- [ ] Servo has adequate power (servos can draw significant current)
- [ ] Power supply is 5V (or appropriate for your servo)
- [ ] Power supply can provide enough current (typically 1-2A for servos)

### 4. Software
- [ ] gpiozero is installed: `pip3 list | grep gpiozero`
- [ ] No other programs are using GPIO 25
- [ ] Run with sudo if permission errors occur

## Quick Manual Test

You can also test servo 2 manually from Python:

```python
from gpiozero import AngularServo
import time

# Initialize servo
servo = AngularServo(25, min_angle=0, max_angle=180, 
                     min_pulse_width=0.0005, max_pulse_width=0.0025)

# Test positions
print("Moving to 0°")
servo.angle = 0
time.sleep(2)

print("Moving to 90°")
servo.angle = 90
time.sleep(2)

print("Moving to 180°")
servo.angle = 180
time.sleep(2)

servo.close()
print("Done")
```

## If Servo 2 is a Continuous Rotation Servo

If your servo 2 is actually a **continuous rotation servo** (360° servo), then:
- Angle 0° = full speed clockwise
- Angle 90° = stop
- Angle 180° = full speed counter-clockwise

In this case, the test should show the servo spinning rather than moving to positions.

## Next Steps

1. Try **Option 1** first (test_servo2.py) - simplest test
2. Check the **Troubleshooting Checklist** above
3. If still not working, install pigpio and try **Option 3**
4. Report back what you observe (does servo move at all? does it jitter? no movement?)
