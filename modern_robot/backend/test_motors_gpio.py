import time
try:
    import RPi.GPIO as GPIO
except ImportError:
    print("Error: RPi.GPIO not found")
    exit(1)

print("Setting up GPIO...")
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Pins
L1 = 24
L2 = 23
R1 = 5
R2 = 6

GPIO.setup(L1, GPIO.OUT)
GPIO.setup(L2, GPIO.OUT)
GPIO.setup(R1, GPIO.OUT)
GPIO.setup(R2, GPIO.OUT)

pL1 = GPIO.PWM(L1, 100)
pL2 = GPIO.PWM(L2, 100)
pR1 = GPIO.PWM(R1, 100)
pR2 = GPIO.PWM(R2, 100)

pL1.start(0)
pL2.start(0)
pR1.start(0)
pR2.start(0)

print("Moving Forward...")
pL1.ChangeDutyCycle(50)
pR1.ChangeDutyCycle(50)
time.sleep(1)

print("Stopping...")
pL1.ChangeDutyCycle(0)
pR1.ChangeDutyCycle(0)

print("Moving Backward...")
pL2.ChangeDutyCycle(50)
pR2.ChangeDutyCycle(50)
time.sleep(1)

print("Stopping...")
pL2.ChangeDutyCycle(0)
pR2.ChangeDutyCycle(0)

pL1.stop()
pL2.stop()
pR1.stop()
pR2.stop()
GPIO.cleanup()
print("Done.")







