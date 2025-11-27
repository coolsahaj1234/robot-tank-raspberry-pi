from app.core.config import settings
try:
    from gpiozero import AngularServo
    from gpiozero.pins.lgpio import LGPIOFactory
except ImportError:
    AngularServo = None
    LGPIOFactory = None

class ServoController:
    def __init__(self):
        self.servos = {}
        
        if settings.MOCK_MODE or AngularServo is None:
            print("ServoController started in MOCK mode")
            return

        # Attempt to use LGPIO factory for Pi 5 compatibility
        try:
            factory = LGPIOFactory()
        except Exception:
            factory = None
            print("LGPIO Factory not available, using default")

        # Configuration for servos
        # 0: Arm Up/Down (GPIO 12)
        # 1: Claw (GPIO 13)
        # 2: Rear Camera (GPIO 19)
        self.servo_config = {
            "arm_lift": 12,
            "claw": 13,
            "rear_cam": 19
        }

        for name, pin in self.servo_config.items():
            try:
                # min_pulse and max_pulse might need tuning for specific servos
                self.servos[name] = AngularServo(
                    pin, 
                    min_angle=0, 
                    max_angle=180,
                    min_pulse_width=0.0005,
                    max_pulse_width=0.0025,
                    pin_factory=factory
                )
            except Exception as e:
                print(f"Failed to initialize servo {name} on pin {pin}: {e}")

    def set_angle(self, name: str, angle: float):
        """
        Set servo angle (0-180)
        """
        if settings.MOCK_MODE:
            print(f"MOCK SERVO: {name} -> {angle}")
            return

        if name in self.servos:
            try:
                # Clamp angle
                angle = max(0, min(180, angle))
                self.servos[name].angle = angle
            except Exception as e:
                print(f"Error setting servo {name}: {e}")
        else:
            print(f"Servo {name} not found")

    def stop(self):
        for servo in self.servos.values():
            servo.detach()

