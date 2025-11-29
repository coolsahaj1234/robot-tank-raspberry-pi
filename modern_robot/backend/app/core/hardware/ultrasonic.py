from app.core.config import settings
try:
    from gpiozero import DistanceSensor
except ImportError:
    DistanceSensor = None

class UltrasonicSystem:
    def __init__(self):
        self.front_sensor = None
        self.rear_sensor = None
        
        if settings.MOCK_MODE or DistanceSensor is None:
            print("UltrasonicSystem started in MOCK mode")
            return

        # Initialize Front Sensor (Trigger 27, Echo 22)
        try:
            self.front_sensor = DistanceSensor(echo=22, trigger=27, max_distance=3)
            print("Front Ultrasonic Sensor initialized")
        except Exception as e:
            print(f"Failed to initialize front ultrasonic: {e}")

        # Initialize Rear Sensor (Trigger 25, Echo 18)
        try:
            self.rear_sensor = DistanceSensor(echo=18, trigger=25, max_distance=3)
            print("Rear Ultrasonic Sensor initialized")
        except Exception as e:
            print(f"Failed to initialize rear ultrasonic: {e}")

    def get_distances(self):
        """Returns dict with front and rear distances in cm"""
        if settings.MOCK_MODE:
            import random
            return {
                "front": round(random.uniform(10, 200), 1),
                "rear": round(random.uniform(10, 200), 1)
            }
            
        distances = {
            "front": None,
            "rear": None
        }

        if self.front_sensor:
            try:
                distances["front"] = round(self.front_sensor.distance * 100, 1)
            except Exception:
                pass
                
        if self.rear_sensor:
            try:
                distances["rear"] = round(self.rear_sensor.distance * 100, 1)
            except Exception:
                pass
                
        return distances

    def close(self):
        if self.front_sensor:
            self.front_sensor.close()
        if self.rear_sensor:
            self.rear_sensor.close()


