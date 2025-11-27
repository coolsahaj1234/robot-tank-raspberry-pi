#!/usr/bin/env python3
"""
Servo 2 Installation and Verification Test (GPIO 19)
This script helps you install the servo arm correctly and then verifies functionality.
"""

from servo import Servo
import time

print("=" * 70)
print("SERVO 2 ARM INSTALLATION & VERIFICATION (GPIO 19)")
print("=" * 70)

servo = Servo()

print(f"\nPCB Version: {servo.pcb_version}")
print("Servo 2 is on GPIO 19 (Hardware PWM)")

# Step 1: Move servo to starting position for installation
print("\n" + "=" * 70)
print("STEP 1: PREPARING SERVO FOR ARM INSTALLATION")
print("=" * 70)
print("\nMoving servo to 0° (starting position)...")
servo.setServoAngle('2', 0)
time.sleep(1)

print("\n📋 SERVO ARM INSTALLATION INSTRUCTIONS:")
print("-" * 70)
print("1. The servo is now at 0° (starting position)")
print("2. Attach the servo arm/horn to the servo shaft")
print("3. Position the arm so it points in your desired 'start' direction")
print("   (This will be the 0° position)")
print("4. The arm will be able to rotate 180° from this position")
print("5. Secure the arm with the screw provided with your servo")
print("\n💡 TIP: For a camera mount or sensor:")
print("   - Install the arm pointing straight up or to one side")
print("   - This gives you a full 180° sweep range")
print("-" * 70)

# Wait for user confirmation
print("\n⏸️  Press ENTER when you have finished installing the arm...")
input()

# Step 2: Verification test
print("\n" + "=" * 70)
print("STEP 2: VERIFICATION TEST")
print("=" * 70)
print("\nStarting verification test...")
print("Watch servo 2 - it should move through these positions:\n")

try:
    # Test sequence - full 180° range
    positions = [
        (0, "Starting position (0°)"),
        (45, "Quarter rotation (45°)"),
        (90, "Half rotation (90°)"),
        (135, "Three-quarter rotation (135°)"),
        (180, "Full rotation (180°)"),
        (90, "Back to center (90°)"),
        (0, "Back to start (0°)")
    ]
    
    for angle, description in positions:
        print(f"  → {description}")
        servo.setServoAngle('2', angle)
        time.sleep(2)
    
    print("\n" + "=" * 70)
    print("✓ SUCCESS! Servo 2 is working correctly on GPIO 19")
    print("=" * 70)
    
    # Continuous sweep demo
    print("\nBonus: 3-second continuous sweep demo (0° to 180°)...")
    start_time = time.time()
    angle = 0
    direction = 1
    
    while time.time() - start_time < 3:
        servo.setServoAngle('2', angle)
        angle += direction * 5
        if angle >= 180:
            direction = -1
        elif angle <= 0:
            direction = 1
        time.sleep(0.05)
    
    # Return to starting position
    servo.setServoAngle('2', 0)
    print("\n✓ Verification complete - Servo 2 is fully functional!")
    print("  Servo returned to starting position (0°)")
    
except KeyboardInterrupt:
    print("\n\nTest interrupted")
    servo.setServoAngle('2', 0)

except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nIf you see an error, check:")
    print("  1. Servo is connected to the '19' connector on the board")
    print("  2. Servo has external power supply")
    print("  3. Ground is shared between Pi and power supply")

print("\n" + "=" * 70)
print("Test complete!")
print("=" * 70)
