from app.core.config import settings
try:
    from gpiozero import Motor
except ImportError:
    Motor = None

class MotorController:
    def __init__(self):
        if settings.MOCK_MODE or Motor is None:
            print("MotorController started in MOCK mode")
            self.left_motor = None
            self.right_motor = None
        else:
            # Pin configuration based on Freenove Tank
            # Left: 24, 23 | Right: 5, 6
            try:
                self.left_motor = Motor(forward=24, backward=23)
                self.right_motor = Motor(forward=5, backward=6)
                print("MotorController initialized with gpiozero")
            except Exception as e:
                print(f"Failed to initialize motors: {e}")
                self.left_motor = None
                self.right_motor = None

    def move(self, x: float, y: float):
        """
        Arcade drive control.
        x: Turn (-1.0 to 1.0)
        y: Throttle (-1.0 to 1.0)
        """
        if settings.MOCK_MODE or not self.left_motor:
            return

        # Calculate left and right motor speeds
        # Simple arcade drive logic
        left_speed = y + x
        right_speed = y - x

        # Normalize
        left_speed = max(-1.0, min(1.0, left_speed))
        right_speed = max(-1.0, min(1.0, right_speed))

        self._set_motor(self.left_motor, left_speed)
        self._set_motor(self.right_motor, right_speed)

    def _set_motor(self, motor, speed):
        if speed > 0:
            motor.forward(speed)
        elif speed < 0:
            motor.backward(-speed)
        else:
            motor.stop()

    def stop(self):
        if self.left_motor:
            self.left_motor.stop()
        if self.right_motor:
            self.right_motor.stop()

