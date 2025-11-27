# Servo 2 Not Moving - Hardware Troubleshooting Guide

## ✅ What We've Confirmed
- GPIO 25 is working correctly
- PWM signals are being sent properly
- Software is functioning as expected

## ❌ Problem
Servo 2 shows **no movement at all** despite correct signals

## 🔍 Root Cause Analysis

Since the GPIO and software are working, the issue is **hardware-related**. Here are the most likely causes:

---

## 1. ⚡ POWER SUPPLY (Most Common Issue)

### Problem
Servos require significant current (500mA - 2A) that the Raspberry Pi **cannot provide**.

### Solution
✅ **Use an external 5V power supply for the servo**

### Correct Wiring
```
Servo Signal Wire (Orange/Yellow) → GPIO 25 (Pin 22) on Pi
Servo Power Wire (Red)            → External 5V Power Supply (+)
Servo Ground Wire (Brown/Black)   → External 5V Power Supply (-)
                                  → ALSO connect to Pi Ground (Pin 6, 9, 14, 20, 25, 30, 34, or 39)
```

### Important
- **DO NOT** power servo from Pi's 5V pin (Pin 2 or 4)
- **MUST** share ground between Pi and external power supply
- Power supply should provide at least 2A

### Recommended Power Sources
- 4x AA battery pack (6V - most servos tolerate this)
- 5V 2A USB power adapter
- Dedicated servo power supply
- LiPo battery with 5V regulator

---

## 2. 🔌 CONNECTION ISSUES

### Check These Connections

#### Servo to Pi
| Servo Wire | Color (typical) | Connects To |
|------------|----------------|-------------|
| Signal     | Orange/Yellow  | GPIO 25 (Physical Pin 22) |
| Power      | Red            | External 5V+ (NOT Pi!) |
| Ground     | Brown/Black    | Ground (shared) |

#### Physical Pin Layout
```
Pi GPIO Header (looking at Pi with USB ports at bottom):

     3V3  [ 1] [ 2]  5V
   GPIO2  [ 3] [ 4]  5V
   GPIO3  [ 5] [ 6]  GND
   GPIO4  [ 7] [ 8]  GPIO14
     GND  [ 9] [10]  GPIO15
  GPIO17  [11] [12]  GPIO18
  GPIO27  [13] [14]  GND
  GPIO22  [15] [16]  GPIO23
     3V3  [17] [18]  GPIO24
  GPIO10  [19] [20]  GND
   GPIO9  [21] [22]  GPIO25  ← SERVO SIGNAL HERE
  GPIO11  [23] [24]  GPIO8
     GND  [25] [26]  GPIO7
```

### Verification Steps
1. Physically trace the wire from servo to Pi
2. Ensure wire is fully inserted into connector
3. Check for loose connections
4. Try a different jumper wire

---

## 3. 🔧 SERVO ISSUES

### Is the Servo Working?

#### Test 1: Swap Servos
- Try connecting a servo that you **know works** to GPIO 25
- If it works → original servo is faulty
- If it doesn't work → connection issue

#### Test 2: Try Servo 2 on Different Pin
- Connect servo 2 to GPIO 12 or 13 (where servo 0/1 work)
- Modify test script to use that GPIO
- If it works → GPIO 25 might have an issue
- If it doesn't work → servo is faulty

#### Test 3: Manual Test
- Disconnect servo from Pi
- Connect servo directly to power (5V and GND only)
- Servo should move to a default position
- If no movement → servo is dead

### Servo Type Check
Is this a **continuous rotation servo**?
- Continuous rotation servos spin rather than move to positions
- They use angle as speed/direction control
- 0° = full speed one way
- 90° = stop
- 180° = full speed other way

---

## 4. 🔋 POWER SUPPLY VERIFICATION

### Measure Voltage
Use a multimeter to check:
- External power supply outputs 5V (±0.5V acceptable)
- Voltage doesn't drop when servo is connected
- Ground connection is solid

### Current Capacity
- Servo can draw 500mA - 2A when moving
- Power supply must handle this
- Insufficient current = servo won't move

---

## 5. 🎯 QUICK DIAGNOSTIC TESTS

### Test A: LED Test (Verify GPIO 25 Output)
```bash
cd /home/pi5/Documents/Robot_Kit_for_Raspberry_Pi-main/Code/Server
python3 verify_gpio25.py
```
Connect an LED (with resistor) to GPIO 25 - it should blink.

### Test B: Servo on Known-Good Pin
Temporarily connect servo 2 to GPIO 12 and test with servo 0 code.

### Test C: Known-Good Servo on GPIO 25
Use servo 0 or 1 (if working) and connect to GPIO 25.

---

## 📋 Systematic Troubleshooting Checklist

Work through this checklist in order:

- [ ] **Step 1**: Verify servo has external power supply (NOT from Pi)
- [ ] **Step 2**: Confirm ground is shared between Pi and power supply
- [ ] **Step 3**: Check signal wire is on GPIO 25 (Physical Pin 22)
- [ ] **Step 4**: Measure power supply voltage (should be ~5V)
- [ ] **Step 5**: Try a different servo on GPIO 25
- [ ] **Step 6**: Try servo 2 on GPIO 12 or 13
- [ ] **Step 7**: Check all wire connections are secure
- [ ] **Step 8**: Verify servo type (standard vs continuous rotation)
- [ ] **Step 9**: Test servo manually (power only, no signal)
- [ ] **Step 10**: Replace jumper wires

---

## 🛠️ Testing Commands

### Run RPi.GPIO Test (Most Reliable)
```bash
cd /home/pi5/Documents/Robot_Kit_for_Raspberry_Pi-main/Code/Server
python3 test_servo2_rpi_gpio.py
```

### Verify GPIO 25 Works
```bash
python3 verify_gpio25.py
```

### Simple gpiozero Test
```bash
python3 test_servo2.py
```

---

## 💡 Most Likely Solutions

Based on "no movement at all", the issue is probably:

### 1. **No External Power** (80% probability)
   - Servo needs its own power supply
   - Cannot run from Pi's power

### 2. **Wrong Pin** (10% probability)
   - Signal wire not actually on GPIO 25
   - Double-check physical pin 22

### 3. **Dead Servo** (10% probability)
   - Servo is faulty
   - Test with a different servo

---

## 📞 Next Steps

Please check:
1. **Do you have an external power supply connected to the servo?**
2. **What color wires does your servo have and where are they connected?**
3. **Can you try a different servo that you know works?**

Let me know the answers and I can help you further!
