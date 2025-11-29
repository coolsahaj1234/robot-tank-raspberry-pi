#!/usr/bin/env python3
"""
GPIO Pin Status Checker for Raspberry Pi Robot Tank
This script displays the current GPIO pin usage based on the robot's configuration.
"""

import json
import os

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# GPIO pin assignments based on PCB v2, Pi v2
USED_PINS = {
    # Motors
    5: "Right Motor - Forward",
    6: "Right Motor - Backward",
    23: "Left Motor - Backward",
    24: "Left Motor - Forward",
    
    # Servos (Hardware PWM)
    12: "Servo 0 (PWM0) - Pan/Tilt",
    13: "Servo 1 (PWM1) - Pan/Tilt",
    19: "Servo 2 (PWM3) - 360° Rotation",
    
    # Ultrasonic Sensor
    22: "Ultrasonic Echo",
    27: "Ultrasonic Trigger",
    
    # Infrared Sensors (PCB v2)
    16: "IR Sensor 1",
    26: "IR Sensor 2",
    21: "IR Sensor 3",
    
    # LED Strip (SPI0)
    10: "SPI0-MOSI (WS2812 Data)",
    11: "SPI0-SCLK (WS2812 Clock)",
    8: "SPI0-CE0",
    9: "SPI0-MISO",
}

AVAILABLE_PINS = {
    0: "I2C0 SDA (can be GPIO)",
    1: "I2C0 SCL (can be GPIO)",
    2: "General Purpose GPIO",
    3: "General Purpose GPIO",
    4: "General Purpose GPIO",
    7: "SPI0-CE1 (can be GPIO)",
    14: "UART TX (can be GPIO)",
    15: "UART RX (can be GPIO)",
    17: "General Purpose GPIO",
    18: "PWM0 alternate (can be GPIO)",
    20: "General Purpose GPIO",
    25: "General Purpose GPIO",
}

def print_header():
    """Print the header for the GPIO status display."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}  Raspberry Pi Robot Tank - GPIO Pin Status{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}\n")

def print_used_pins():
    """Print all currently used GPIO pins."""
    print(f"{Colors.BOLD}{Colors.FAIL}USED GPIO PINS ({len(USED_PINS)} pins):{Colors.ENDC}")
    print(f"{Colors.FAIL}{'─'*70}{Colors.ENDC}")
    
    # Group by category
    categories = {
        "Motors": [5, 6, 23, 24],
        "Servos": [12, 13, 19],
        "Ultrasonic": [22, 27],
        "Infrared": [16, 21, 26],
        "LED/SPI": [8, 9, 10, 11],
    }
    
    for category, pins in categories.items():
        print(f"\n{Colors.BOLD}{Colors.WARNING}  {category}:{Colors.ENDC}")
        for pin in sorted(pins):
            if pin in USED_PINS:
                print(f"    {Colors.FAIL}GPIO {pin:2d}{Colors.ENDC} → {USED_PINS[pin]}")

def print_available_pins():
    """Print all available GPIO pins."""
    print(f"\n\n{Colors.BOLD}{Colors.OKGREEN}AVAILABLE GPIO PINS ({len(AVAILABLE_PINS)} pins):{Colors.ENDC}")
    print(f"{Colors.OKGREEN}{'─'*70}{Colors.ENDC}\n")
    
    for pin in sorted(AVAILABLE_PINS.keys()):
        print(f"  {Colors.OKGREEN}GPIO {pin:2d}{Colors.ENDC} → {AVAILABLE_PINS[pin]}")

def print_summary():
    """Print a summary of pin usage."""
    total_gpio = 28  # GPIO 0-27 are commonly used
    used_count = len(USED_PINS)
    available_count = len(AVAILABLE_PINS)
    
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}{'─'*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKCYAN}SUMMARY:{Colors.ENDC}")
    print(f"  Total GPIO pins (0-27): {total_gpio}")
    print(f"  {Colors.FAIL}Used pins: {used_count}{Colors.ENDC}")
    print(f"  {Colors.OKGREEN}Available pins: {available_count}{Colors.ENDC}")
    print(f"  Other/Reserved: {total_gpio - used_count - available_count}")
    print(f"{Colors.BOLD}{Colors.OKCYAN}{'─'*70}{Colors.ENDC}\n")

def print_recommendations():
    """Print recommendations for adding new components."""
    print(f"{Colors.BOLD}{Colors.OKBLUE}RECOMMENDATIONS FOR NEW COMPONENTS:{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'─'*70}{Colors.ENDC}")
    
    recommendations = [
        ("Additional Sensors", "GPIO 2, 3, 4, 17, 20, or 25"),
        ("I2C Devices (OLED, IMU)", "GPIO 0 (SDA) and GPIO 1 (SCL)"),
        ("Serial/UART Devices", "GPIO 14 (TX) and GPIO 15 (RX)"),
        ("Additional PWM", "GPIO 18 (PWM0 alternate)"),
        ("Simple Digital I/O", "Any available GPIO pin"),
    ]
    
    for component, pins in recommendations:
        print(f"\n  {Colors.BOLD}{component}:{Colors.ENDC}")
        print(f"    → {pins}")
    
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}{'='*70}{Colors.ENDC}\n")

def check_config():
    """Check the current PCB and Pi version from params.json."""
    try:
        params_path = os.path.join(os.path.dirname(__file__), "Server", "params.json")
        with open(params_path, 'r') as f:
            params = json.load(f)
            pcb_version = params.get("Pcb_Version", "Unknown")
            pi_version = params.get("Pi_Version", "Unknown")
            
            print(f"{Colors.BOLD}Configuration:{Colors.ENDC}")
            print(f"  PCB Version: {pcb_version}")
            print(f"  Raspberry Pi Version: {pi_version}")
            
            if pcb_version != 2 or pi_version != 2:
                print(f"\n{Colors.WARNING}⚠️  Warning: This pin mapping is for PCB v2 and Pi v2{Colors.ENDC}")
                print(f"{Colors.WARNING}   Your configuration may differ!{Colors.ENDC}")
    except FileNotFoundError:
        print(f"{Colors.WARNING}⚠️  Could not find params.json{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.WARNING}⚠️  Error reading config: {e}{Colors.ENDC}")

def main():
    """Main function to display GPIO pin status."""
    print_header()
    check_config()
    print_used_pins()
    print_available_pins()
    print_summary()
    print_recommendations()

if __name__ == "__main__":
    main()
