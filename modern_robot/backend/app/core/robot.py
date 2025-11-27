from typing import Dict, Any, Optional
import asyncio
from enum import Enum
from app.core.config import settings
from app.services.ai_service import AIService
from app.core.hardware.motors import MotorController
from app.core.hardware.servos import ServoController
from app.core.hardware.camera import CameraManager

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
        
        # Start sensor loops, AI processing loops etc.
        if settings.MOCK_MODE:
             asyncio.create_task(self._mock_sensor_loop())

    async def stop(self):
        self.is_running = False
        await self.ai_service.stop()
        self.camera_manager.stop()
        self.motors.stop()
        self.servos.stop()
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
        # print(f"Moving robot: x={x}, y={y}")
        self.motors.move(x, y)

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
        
        servo_map = {
            'lift': 'arm_lift',
            'claw': 'claw'
        }
        
        if joint in servo_map:
            print(f"Moving arm {joint} to {value}")
            self.servos.set_angle(servo_map[joint], value)

    async def _stop_movement(self):
        print("Stopping all movement")
        self.motors.stop()
        
    async def _mock_sensor_loop(self):
        """Updates mock sensor data periodically"""
        while self.is_running:
            import random
            self.state["sensors"]["ultrasonic"] = random.uniform(10, 200)
            self.state["battery"] = max(0, self.state["battery"] - 0.01)
            
            if self.emit_status_callback:
                await self.emit_status_callback(self.state)
                
            await asyncio.sleep(1)

# Global Robot Instance
robot = Robot()
