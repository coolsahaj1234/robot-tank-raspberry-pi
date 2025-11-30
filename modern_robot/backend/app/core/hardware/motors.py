import time
from app.core.config import settings
try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

class MotorController:
    def __init__(self):
        self.speed_scale = 1.0
        
        if settings.MOCK_MODE or GPIO is None:
            print("MotorController started in MOCK mode")
            self.pwm_L1 = None
            self.pwm_L2 = None
            self.pwm_R1 = None
            self.pwm_R2 = None
            return

        print("MotorController initializing with RPi.GPIO (matching Server/motor.py)")
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Pin Definitions (from Code/Server/motor.py)
        self.L_pin1 = 24  # Left Forward
        self.L_pin2 = 23  # Left Backward
        self.R_pin1 = 5   # Right Forward
        self.R_pin2 = 6   # Right Backward
        
        try:
            # Setup pins
            GPIO.setup(self.L_pin1, GPIO.OUT)
            GPIO.setup(self.L_pin2, GPIO.OUT)
            GPIO.setup(self.R_pin1, GPIO.OUT)
            GPIO.setup(self.R_pin2, GPIO.OUT)
            
            # Initialize PWM (100Hz)
            self.pwm_L1 = GPIO.PWM(self.L_pin1, 100)
            self.pwm_L2 = GPIO.PWM(self.L_pin2, 100)
            self.pwm_R1 = GPIO.PWM(self.R_pin1, 100)
            self.pwm_R2 = GPIO.PWM(self.R_pin2, 100)
            
            # Start with 0
            self.pwm_L1.start(0)
            self.pwm_L2.start(0)
            self.pwm_R1.start(0)
            self.pwm_R2.start(0)
            
            print("Motors initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize motors with RPi.GPIO: {e}")
            self.pwm_L1 = None

    def set_speed_scale(self, scale: float):
        """Set the global speed scaling factor (0.0 to 1.0)"""
        self.speed_scale = max(0.0, min(1.0, scale))
        # print(f"Motor speed scale set to {self.speed_scale}")

    def move(self, x: float, y: float):
        """
        Arcade drive control.
        x: Turn (-1.0 to 1.0)
        y: Throttle (-1.0 to 1.0)
        """
        if settings.MOCK_MODE or not self.pwm_L1:
            return

        # Calculate raw speeds
        # y is throttle (forward/back), x is turn (left/right)
        # Standard arcade drive mixing
        left_val = y + x
        right_val = y - x

        # Normalize to -1.0 to 1.0
        left_val = max(-1.0, min(1.0, left_val))
        right_val = max(-1.0, min(1.0, right_val))

        # Apply speed scaling
        left_val *= self.speed_scale
        right_val *= self.speed_scale

        # Convert to Duty Cycle (0-100)
        self._set_motor_pwm("left", left_val)
        self._set_motor_pwm("right", right_val)

    def _set_motor_pwm(self, side, value):
        # Value is -1.0 to 1.0
        duty = abs(value) * 100
        if duty > 100: duty = 100
        
        if side == "left":
            pwm_fwd = self.pwm_L1
            pwm_back = self.pwm_L2
        else:
            pwm_fwd = self.pwm_R1
            pwm_back = self.pwm_R2
            
        if value > 0: # Forward
            pwm_fwd.ChangeDutyCycle(duty)
            pwm_back.ChangeDutyCycle(0)
        elif value < 0: # Backward
            pwm_fwd.ChangeDutyCycle(0)
            pwm_back.ChangeDutyCycle(duty)
        else: # Stop
            pwm_fwd.ChangeDutyCycle(0)
            pwm_back.ChangeDutyCycle(0)

    def stop(self):
        if self.pwm_L1:
            self.pwm_L1.ChangeDutyCycle(0)
            self.pwm_L2.ChangeDutyCycle(0)
            self.pwm_R1.ChangeDutyCycle(0)
            self.pwm_R2.ChangeDutyCycle(0)

    def close(self):
        self.stop()
        if self.pwm_L1:
            self.pwm_L1.stop()
            self.pwm_L2.stop()
            self.pwm_R1.stop()
            self.pwm_R2.stop()
            # We don't cleanup GPIO here to avoid messing with other components
