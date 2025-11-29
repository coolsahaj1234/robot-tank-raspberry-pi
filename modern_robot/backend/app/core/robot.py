from typing import Dict, Any, Optional
import asyncio
from enum import Enum
from app.core.config import settings
from app.services.ai_service import AIService
from app.core.hardware.motors import MotorController
from app.core.hardware.servos import ServoController
from app.core.hardware.camera import CameraManager
from app.core.hardware.ultrasonic import UltrasonicSystem

class AutonomyLevel(str, Enum):
    MANUAL = "manual"
    SEMI_AUTO = "semi"
    FULL_AUTO = "auto"

class Robot:
    def __init__(self):
        self.state = {
            "autonomy_level": AutonomyLevel.MANUAL,
            "battery": 100,
            "status": "standby",
            "sensors": {},
            "active_modules": []
        }
        self.is_running = False
        
        # Initialize subsystems
        self.motors = MotorController()
        self.servos = ServoController()
        self.camera_manager = CameraManager()
        self.ultrasonic = UltrasonicSystem()
        self.ai_service = AIService()
        self.emit_status_callback = None
        
        print(f"Robot initialized in {'MOCK' if settings.MOCK_MODE else 'REAL'} mode.")

    def set_emit_status_callback(self, callback):
        self.emit_status_callback = callback

    async def start(self):
        self.is_running = True
        print("Robot systems started.")
        self.camera_manager.start()
        await self.ai_service.start()
        
        # Start sensor loops
        asyncio.create_task(self._sensor_loop())

    async def stop(self):
        self.is_running = False
        await self.ai_service.stop()
        self.camera_manager.stop()
        self.motors.stop()
        self.servos.stop()
        self.ultrasonic.close()
        print("Robot systems stopped.")

    def get_state(self) -> Dict[str, Any]:
        return self.state

    def set_autonomy_level(self, level: str):
        if level in [l.value for l in AutonomyLevel]:
            self.state["autonomy_level"] = level
            print(f"Autonomy level set to: {level}")
        else:
            print(f"Invalid autonomy level: {level}")

    async def execute_command(self, command_data: Dict[str, Any]):
        cmd = command_data.get('command')
        params = command_data.get('params', {})
        
        # print(f"Executing command: {cmd} with params: {params}")
        
        if self.state["autonomy_level"] == AutonomyLevel.FULL_AUTO:
            if cmd == "emergency_stop":
                await self._stop_movement()
            else:
                print("Ignored manual command in FULL_AUTO mode (except emergency stop)")
            return

        if cmd == "move":
            await self._handle_move(params)
        elif cmd == "camera_pan":
            await self._handle_camera_pan(params)
        elif cmd == "arm_control":
            await self._handle_arm_control(params)
        # Add more command handlers

    async def _handle_move(self, params):
        # x, y usually from joystick (-1 to 1)
        x = params.get('x', 0)
        y = params.get('y', 0)
        
        # Situational Awareness / Collision Avoidance
        # Only intervene if moving significantly (abs > 0.1)
        if self.state["autonomy_level"] in [AutonomyLevel.SEMI_AUTO, AutonomyLevel.FULL_AUTO]:
            distances = self.state["sensors"].get("ultrasonic", {})
            front_dist = distances.get("front")
            rear_dist = distances.get("rear")
            
            # Stop if too close (< 15cm)
            if y > 0 and front_dist is not None and front_dist < 15:
                print(f"Safety Stop: Obstacle in front ({front_dist}cm)")
                self.motors.stop()
                self.state["status"] = "blocked front"
                if self.emit_status_callback:
                    await self.emit_status_callback(self.state)
                return

            if y < 0 and rear_dist is not None and rear_dist < 15:
                print(f"Safety Stop: Obstacle behind ({rear_dist}cm)")
                self.motors.stop()
                self.state["status"] = "blocked rear"
                if self.emit_status_callback:
                    await self.emit_status_callback(self.state)
                return

        if x == 0 and y == 0:
             self.state["status"] = "standby"
             self.motors.stop()
        else:
             self.state["status"] = "moving"
             self.motors.move(x, y)
             
        if self.emit_status_callback:
            await self.emit_status_callback(self.state)

    async def _handle_camera_pan(self, params):
        # Controls the rear camera servo (Servo 2 / GPIO 19)
        # Expecting angle 0-180
        angle = params.get('angle', 90)
        print(f"Panning camera to {angle}")
        self.servos.set_angle("rear_cam", angle)

    async def _handle_arm_control(self, params):
        # Controls Arm (Servo 0) and Claw (Servo 1)
        joint = params.get('joint') # 'lift' or 'claw'
        value = params.get('value') # 0-180
        
        self.state["status"] = "operating arm"
        if self.emit_status_callback:
            await self.emit_status_callback(self.state)
        
        servo_map = {
            'lift': 'arm_lift',
            'claw': 'claw'
        }
        
        if joint in servo_map:
            print(f"Moving arm {joint} to {value}")
            self.servos.set_angle(servo_map[joint], value)
            
        # Reset to standby after a short delay (simulating action completion)
        await asyncio.sleep(0.5)
        self.state["status"] = "standby"
        if self.emit_status_callback:
            await self.emit_status_callback(self.state)

    async def _stop_movement(self):
        print("Stopping all movement")
        self.motors.stop()
        self.state["status"] = "standby"
        if self.emit_status_callback:
            await self.emit_status_callback(self.state)
        
    async def _sensor_loop(self):
        """Updates sensor data periodically"""
        while self.is_running:
            # Update Ultrasonic
            self.state["sensors"]["ultrasonic"] = self.ultrasonic.get_distances()
            
            # Simulate battery drain or read from ADC if implemented
            self.state["battery"] = max(0, self.state["battery"] - 0.001)
            
            if self.emit_status_callback:
                await self.emit_status_callback(self.state)
                
            await asyncio.sleep(0.5) # Update rate 2Hz

# Global Robot Instance
robot = Robot()
