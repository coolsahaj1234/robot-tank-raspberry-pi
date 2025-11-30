from app.core.config import settings
try:
    from gpiozero import LineSensor
except ImportError:
    LineSensor = None

class InfraredSystem:
    def __init__(self):
        self.sensors = []
        if settings.MOCK_MODE or LineSensor is None:
            print("InfraredSystem started in MOCK mode")
            return

        # Freenove Robot V2 GPIO mapping for IR Sensors
        # IR01 (Left) -> GPIO 16
        # IR02 (Center) -> GPIO 26 (Check version 2 mapping from infrared.py)
        # IR03 (Right) -> GPIO 21
        
        # NOTE: Original infrared.py logic checks PCB version.
        # PCB 1: 16, 20, 21
        # PCB 2: 16, 26, 21
        # We'll assume PCB 2 mostly, but can try-catch 20 if 26 fails or vice versa? 
        # Actually, let's just stick to the PCB 2 mapping (16, 26, 21) as it's "modern" robot.
        
        try:
            self.ir_left = LineSensor(16)
            self.ir_center = LineSensor(26)
            self.ir_right = LineSensor(21)
            self.sensors = [self.ir_left, self.ir_center, self.ir_right]
            print("Infrared Sensors initialized (GPIO 16, 26, 21)")
        except Exception as e:
            print(f"Failed to initialize Infrared sensors: {e}")
            self.sensors = []

    def get_values(self):
        """
        Returns list of booleans [Left, Center, Right]
        True means detecting black line (usually), but gpiozero LineSensor logic:
        - When line is detected (active), value is 1.
        - When no line (reflective surface), value is 0.
        Wait, LineSensor by default:
        - Active (line detected) -> value=1
        Let's verify with original code.
        Original: returns 1 if self.IR01_sensor.value else 0
        """
        if settings.MOCK_MODE or not self.sensors:
            import random
            # Randomly return values
            return [random.choice([True, False]) for _ in range(3)]

        return [sensor.is_active for sensor in self.sensors] # is_active is True when line is detected

    def read_all_infrared_byte(self):
        """Mirror original read_all_infrared returning int"""
        vals = self.get_values()
        # Original: (Left << 2) | (Center << 1) | Right
        # But wait, original code:
        # IR01 (Left?), IR02 (Center?), IR03 (Right?)
        # return (read(1)<<2) | (read(2)<<1) | read(3)
        
        # Let's map:
        v1 = 1 if vals[0] else 0
        v2 = 1 if vals[1] else 0
        v3 = 1 if vals[2] else 0
        
        return (v1 << 2) | (v2 << 1) | v3

    def close(self):
        for sensor in self.sensors:
            sensor.close()







