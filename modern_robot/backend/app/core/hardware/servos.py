from app.core.config import settings
try:
    from rpi_hardware_pwm import HardwarePWM
except ImportError:
    HardwarePWM = None

class ServoController:
    def __init__(self):
        self.servos = {}
        
        if settings.MOCK_MODE or HardwarePWM is None:
            print("ServoController started in MOCK mode (or HardwarePWM missing)")
            return

        print("Initializing HardwareServo (Freenove PCB v2 Protocol)")
        
        # Initialize HardwarePWM instances (Chip 0)
        # Channel 0 -> GPIO 12 (Arm Lift)
        # Channel 1 -> GPIO 13 (Claw)
        # Channel 3 -> GPIO 19 (Rear Cam)
        try:
            print("  - Initializing PWM Channel 0 (GPIO 12)...")
            self.pwm0 = HardwarePWM(pwm_channel=0, hz=50, chip=0) # GPIO 12
            self.pwm0.start(0)
            
            print("  - Initializing PWM Channel 1 (GPIO 13)...")
            self.pwm1 = HardwarePWM(pwm_channel=1, hz=50, chip=0) # GPIO 13
            self.pwm1.start(0)
            
            print("  - Initializing PWM Channel 3 (GPIO 19)...")
            self.pwm3 = HardwarePWM(pwm_channel=3, hz=50, chip=0) # GPIO 19
            self.pwm3.start(0)
            
            self.servos = {
                "arm_lift": self.pwm1,
                "claw": self.pwm0,
                "rear_cam": self.pwm3
            }
            
            # Set Initial Positions exactly like Server/servo.py
            # Channel 0 (Lift): 90
            # Channel 1 (Claw): 140
            # Channel 2/3 (Rear): 90
            print("  - Setting initial servo angles...")
            self.set_angle("arm_lift", 140)
            self.set_angle("claw", 90)
            self.set_angle("rear_cam", 90)
            print("  - Servos initialized successfully.")
            
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to initialize HardwarePWM: {e}")
            print("Falling back to MOCK mode for Servos to allow server startup.")
            self.servos = {} # Empty dict enables mock behavior in set_angle

    def _map(self, x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def set_angle(self, name: str, angle: float):
        """
        Set servo angle (0-180) using HardwarePWM duty cycle mapping.
        Mapping matches Freenove Server/servo.py: 0-180 -> 2.5-12.5% duty
        """
        if settings.MOCK_MODE or name not in self.servos:
            if settings.MOCK_MODE:
                print(f"MOCK SERVO: {name} -> {angle}")
            return

        # Constrain angles based on logic in Server/servo.py
        if name == "arm_lift": # Channel 0
            angle = max(90, min(150, angle))
        elif name == "claw": # Channel 1
            angle = max(90, min(150, angle))
        elif name == "rear_cam": # Channel 2/3
            angle = max(0, min(180, angle))
            
        try:
            duty = self._map(angle, 0, 180, 2.5, 12.5)
            self.servos[name].change_duty_cycle(duty)
        except Exception as e:
            print(f"Error setting servo {name}: {e}")

    def stop(self):
        if settings.MOCK_MODE:
            return
            
        for servo in self.servos.values():
            try:
                servo.stop()
            except:
                pass
