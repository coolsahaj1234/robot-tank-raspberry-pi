# GPIO Pin Usage on Raspberry Pi Robot Tank

**Configuration:** PCB Version 2, Raspberry Pi Version 2 (Pi 5)

## Used GPIO Pins

### Motors (via gpiozero Motor class)
| GPIO Pin | Function | Component |
|----------|----------|-----------|
| GPIO 5   | Right Motor - Forward | Motor Controller |
| GPIO 6   | Right Motor - Backward | Motor Controller |
| GPIO 23  | Left Motor - Backward | Motor Controller |
| GPIO 24  | Left Motor - Forward | Motor Controller |

### Servos (via Hardware PWM)
| GPIO Pin | PWM Channel | Function | Component |
|----------|-------------|----------|-----------|
| GPIO 12  | PWM0 | Servo Channel 0 (Pan/Tilt) | Servo Motor |
| GPIO 13  | PWM1 | Servo Channel 1 (Pan/Tilt) | Servo Motor |
| GPIO 19  | PWM3 | Servo Channel 2 (360° Rotation) | Continuous Servo |

### Ultrasonic Sensor
| GPIO Pin | Function | Component |
|----------|----------|-----------|
| GPIO 22  | Echo Pin | HC-SR04 Ultrasonic Sensor |
| GPIO 27  | Trigger Pin | HC-SR04 Ultrasonic Sensor |

### Infrared Sensors (PCB v2)
| GPIO Pin | Function | Component |
|----------|----------|-----------|
| GPIO 16  | IR Sensor 1 | Line Following Sensor |
| GPIO 26  | IR Sensor 2 | Line Following Sensor |
| GPIO 21  | IR Sensor 3 | Line Following Sensor |

### LED Strip (WS2812 via SPI)
| GPIO Pin | SPI Function | Component |
|----------|--------------|-----------|
| GPIO 10  | SPI0-MOSI (Data) | WS2812 LED Strip |
| GPIO 11  | SPI0-SCLK (Clock) | WS2812 LED Strip |
| GPIO 8   | SPI0-CE0 | WS2812 LED Strip |
| GPIO 9   | SPI0-MISO | WS2812 LED Strip |

### Camera Interfaces
- **CSI Camera Ports**: Used for dual camera setup (cam0 and cam1)
  - These use dedicated CSI interfaces, not GPIO pins

---

## Summary of Used Pins
**Total GPIO Pins Used: 17**

Used: 5, 6, 8, 9, 10, 11, 12, 13, 16, 19, 21, 22, 23, 24, 26, 27

---

## Available (Unused) GPIO Pins

### General Purpose GPIO Pins Available
| GPIO Pin | Notes |
|----------|-------|
| GPIO 0   | Available (I2C0 SDA - can be used as GPIO) |
| GPIO 1   | Available (I2C0 SCL - can be used as GPIO) |
| GPIO 2   | Available |
| GPIO 3   | Available |
| GPIO 4   | Available |
| GPIO 7   | Available (SPI0-CE1 - can be used as GPIO if not using SPI1) |
| GPIO 14  | Available (UART TX - can be used as GPIO) |
| GPIO 15  | Available (UART RX - can be used as GPIO) |
| GPIO 17  | Available |
| GPIO 18  | Available (PWM0 alternate - can be used as GPIO) |
| GPIO 20  | Available |
| GPIO 25  | Available |

### Hardware PWM Capable Pins (Currently Unused)
| GPIO Pin | PWM Channel | Status |
|----------|-------------|--------|
| GPIO 18  | PWM0 | Available (alternate to GPIO 12) |

### Notes on Available Pins:
1. **I2C Pins (GPIO 0, 1)**: Can be used for I2C devices like OLED displays, sensors, etc.
2. **UART Pins (GPIO 14, 15)**: Can be used for serial communication or as regular GPIO
3. **GPIO 2, 3, 4**: Fully available for any purpose
4. **GPIO 7**: Available if you don't need a second SPI chip select
5. **GPIO 17, 20, 25**: Fully available for any purpose

---

## Recommendations for Adding New Components

### If you want to add:
- **Additional Sensors**: Use GPIO 2, 3, 4, 17, 20, or 25
- **I2C Devices** (OLED, IMU, etc.): Use GPIO 0 (SDA) and GPIO 1 (SCL)
- **Serial Devices**: Use GPIO 14 (TX) and GPIO 15 (RX)
- **Additional PWM Devices**: GPIO 18 is available (shares PWM0 with GPIO 12)
- **Simple Digital I/O**: Any of the available pins listed above

### Reserved/Special Pins to Avoid:
- **GPIO 28-45**: These are used for various board functions on Pi 5
- Pins already in use (see "Used GPIO Pins" section above)

---

## Pin Conflicts to Watch For

1. **Hardware PWM**: GPIO 12, 13, 18, 19 share PWM channels. Currently using 12, 13, 19.
2. **SPI0**: GPIO 7-11 are SPI0 pins. Currently using for LED strip.
3. **I2C**: GPIO 0-1 are default I2C pins but can be repurposed.
4. **UART**: GPIO 14-15 are UART pins but can be repurposed if serial console is disabled.

---

## Quick Reference: Raspberry Pi 5 GPIO Pinout

```
     3.3V  (1) (2)  5V
    GPIO2  (3) (4)  5V
    GPIO3  (5) (6)  GND
    GPIO4  (7) (8)  GPIO14
      GND  (9) (10) GPIO15
   GPIO17 (11) (12) GPIO18
   GPIO27 (13) (14) GND
   GPIO22 (15) (16) GPIO23
     3.3V (17) (18) GPIO24
   GPIO10 (19) (20) GND
    GPIO9 (21) (22) GPIO25
   GPIO11 (23) (24) GPIO8
      GND (25) (26) GPIO7
    GPIO0 (27) (28) GPIO1
    GPIO5 (29) (30) GND
    GPIO6 (31) (32) GPIO12
   GPIO13 (33) (34) GND
   GPIO19 (35) (36) GPIO16
   GPIO26 (37) (38) GPIO20
      GND (39) (40) GPIO21
```

**Legend:**
- ✅ = Currently Used
- ⚠️ = Used by SPI/I2C/UART (can be repurposed)
- ✨ = Available for new components
