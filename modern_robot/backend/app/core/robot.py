from typing import Dict, Any, Optional
import asyncio
from enum import Enum
from app.core.config import settings
from app.services.ai_service import AIService
from app.core.hardware.motors import MotorController
from app.core.hardware.servos import ServoController
from app.core.hardware.camera import CameraManager
from app.core.hardware.ultrasonic import UltrasonicSystem
from app.core.hardware.led import LedController
from app.core.hardware.infrared import InfraredSystem

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
            "active_modules": [],
            "speed_limit": 100 # percentage
        }
        self.is_running = False
        self.pickup_task = None
        self.tracking_task = None
        self.line_tracking_task = None
        self.obstacle_avoidance_task = None
        
        # Initialize subsystems
        self.motors = MotorController()
        self.servos = ServoController()
        self.camera_manager = CameraManager()
        self.ultrasonic = UltrasonicSystem()
        self.infrared = InfraredSystem()
        self.leds = LedController()
        self.ai_service = AIService()
        self.emit_status_callback = None
        
        print(f"Robot initialized in {'MOCK' if settings.MOCK_MODE else 'REAL'} mode.")

    def set_emit_status_callback(self, callback):
        self.emit_status_callback = callback

    async def start(self):
        self.is_running = True
        print("Robot systems started.")
        self.camera_manager.start()
        await self.leds.start()
        await self.ai_service.start()
        
        # Set default LED state
        self.leds.set_mode("breath", (0, 255, 0)) # Breathing green on start
        
        # Start sensor loops
        asyncio.create_task(self._sensor_loop())

    async def stop(self):
        self.is_running = False
        await self.ai_service.stop()
        self.camera_manager.stop()
        self.motors.stop()
        self.servos.stop()
        self.ultrasonic.close()
        self.infrared.close()
        await self.leds.stop()
        print("Robot systems stopped.")

    def get_state(self) -> Dict[str, Any]:
        return self.state

    def set_autonomy_level(self, level: str):
        if level in [l.value for l in AutonomyLevel]:
            old_level = self.state["autonomy_level"]
            self.state["autonomy_level"] = level
            print(f"Autonomy level set to: {level}")
            
            # Transition Logic
            if level == AutonomyLevel.FULL_AUTO and old_level != AutonomyLevel.FULL_AUTO:
                 # Auto-start Obstacle Avoidance as default "Auto" behavior
                 print("Entering FULL_AUTO: Starting Obstacle Avoidance")
                 # We use create_task because this isn't an async method
                 loop = asyncio.get_event_loop()
                 loop.create_task(self.execute_command({'command': 'obstacle_avoidance'}))
                 
            elif old_level == AutonomyLevel.FULL_AUTO and level != AutonomyLevel.FULL_AUTO:
                 # Stop any auto tasks when leaving Auto
                 print("Leaving FULL_AUTO: Stopping tasks")
                 loop = asyncio.get_event_loop()
                 loop.create_task(self._cancel_tasks())
                 self.motors.stop()
                 
        else:
            print(f"Invalid autonomy level: {level}")

    def _check_cliff(self) -> bool:
        """
        Returns True if any infrared sensor detects a cliff (no reflection/active).
        Note: LineSensor logic -> Active (True) = Black/No Reflection.
        In normal usage (white table), active means Cliff or Black Line.
        """
        sensors = self.infrared.get_values()
        # If any sensor is True (Active), it means no reflection -> Cliff
        if any(sensors):
            return True
        return False

    async def execute_command(self, command_data: Dict[str, Any]):
        cmd = command_data.get('command')
        params = command_data.get('params', {})
        
        # print(f"Executing command: {cmd} with params: {params}")
        
        # Handle FULL_AUTO restrictions
        if self.state["autonomy_level"] == AutonomyLevel.FULL_AUTO:
            # Allow only high-level AI/autonomous commands and emergency stops
            allowed_cmds = ["emergency_stop", "track_face", "line_tracking", "obstacle_avoidance", "pickup", "drop", "set_speed", "set_led"]
            if cmd not in allowed_cmds:
                print(f"Ignored manual command '{cmd}' in FULL_AUTO mode")
                return

        # Stop special tasks if manual move
        if cmd == "move":
            await self._cancel_tasks()
            await self._handle_move(params)
            
        elif cmd == "set_speed":
            speed_val = params.get('value', 100)
            self._handle_set_speed(speed_val)
            
        elif cmd == "camera_pan":
            await self._handle_camera_pan(params)

        elif cmd == "set_zoom":
            camera = params.get('camera', 'front')
            factor = params.get('factor', 1.0)
            self.camera_manager.set_zoom(camera, float(factor))
            
        elif cmd == "arm_control":
            await self._handle_arm_control(params)
            
        elif cmd == "pickup":
            if self.pickup_task and not self.pickup_task.done():
                 print("Pickup already in progress")
            else:
                 await self._cancel_tasks()
                 self.pickup_task = asyncio.create_task(self._auto_pickup_sequence())
                 
        elif cmd == "drop":
             await self._cancel_tasks()
             await self._handle_drop()
             
        elif cmd == "track_face":
            if self.tracking_task and not self.tracking_task.done():
                self.tracking_task.cancel()
                self.tracking_task = None
                self.state["status"] = "standby"
                if self.emit_status_callback: await self.emit_status_callback(self.state)
            else:
                await self._cancel_tasks()
                self.tracking_task = asyncio.create_task(self._track_face_loop())
        
        elif cmd == "line_tracking":
             if self.line_tracking_task and not self.line_tracking_task.done():
                 self.line_tracking_task.cancel()
                 self.line_tracking_task = None
                 self.state["status"] = "standby"
             else:
                 await self._cancel_tasks()
                 self.line_tracking_task = asyncio.create_task(self._line_tracking_loop())
                 
        elif cmd == "obstacle_avoidance":
             if self.obstacle_avoidance_task and not self.obstacle_avoidance_task.done():
                 self.obstacle_avoidance_task.cancel()
                 self.obstacle_avoidance_task = None
                 self.state["status"] = "standby"
             else:
                 await self._cancel_tasks()
                 self.obstacle_avoidance_task = asyncio.create_task(self._obstacle_avoidance_loop())
                 
        elif cmd == "set_led":
            mode = params.get('mode', 'static')
            r = params.get('r', 0)
            g = params.get('g', 0)
            b = params.get('b', 0)
            self.leds.set_mode(mode, (r, g, b))

    async def _cancel_tasks(self):
        if self.tracking_task: self.tracking_task.cancel(); self.tracking_task = None
        if self.pickup_task: self.pickup_task.cancel(); self.pickup_task = None
        if self.line_tracking_task: self.line_tracking_task.cancel(); self.line_tracking_task = None
        if self.obstacle_avoidance_task: self.obstacle_avoidance_task.cancel(); self.obstacle_avoidance_task = None

    def _handle_set_speed(self, speed_val):
        """Set speed limit percentage (0-100)"""
        try:
            val = float(speed_val)
            val = max(0, min(100, val))
            self.state["speed_limit"] = val
            self.motors.set_speed_scale(val / 100.0)
            print(f"Speed limit set to {val}%")
        except ValueError:
            pass

    async def _handle_move(self, params):
        # x, y usually from joystick (-1 to 1)
        x = params.get('x', 0)
        y = params.get('y', 0)
        
        # CLIFF DETECTION (Safety First)
        # Check if sensors see "Cliff" (No Reflection)
        # BUT only if moving forward or turning (y >= 0 or x != 0)
        # Allow reversing (y < 0) to escape cliff.
        if (y > 0 or (x != 0 and y == 0)) and self._check_cliff():
            print("Cliff detected! Stopping/Preventing movement.")
            self.motors.stop()
            # Maybe back up slightly automatically?
            # self.motors.move(0, -0.2)
            # await asyncio.sleep(0.1)
            # self.motors.stop()
            return
        
        # Situational Awareness / Collision Avoidance for Manual Mode if in Semi/Auto
        if self.state["autonomy_level"] in [AutonomyLevel.SEMI_AUTO, AutonomyLevel.FULL_AUTO]:
            distances = self.state["sensors"].get("ultrasonic", {})
            front_dist = distances.get("front")
            rear_dist = distances.get("rear")
            
            # Stop if too close (< 15cm)
            if y > 0 and front_dist is not None and front_dist < 15:
                # Allow reversing
                self.motors.stop()
                return

            if y < 0 and rear_dist is not None and rear_dist < 15:
                # Allow going forward
                self.motors.stop()
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
        # DISABLED REAR CAMERA
        pass
        # angle = params.get('angle', 90)
        # self.servos.set_angle("rear_cam", angle)

    async def _handle_arm_control(self, params):
        joint = params.get('joint') # 'lift' or 'claw'
        value = params.get('value') # 0-180
        
        self.state["status"] = "operating arm"
        if self.emit_status_callback: await self.emit_status_callback(self.state)
        
        servo_map = {'lift': 'arm_lift', 'claw': 'claw'}
        if joint in servo_map:
            self.servos.set_angle(servo_map[joint], value)
            
        await asyncio.sleep(0.5)
        self.state["status"] = "standby"
        if self.emit_status_callback: await self.emit_status_callback(self.state)

    async def _handle_drop(self):
        print("Dropping object...")
        self.state["status"] = "dropping"
        if self.emit_status_callback: await self.emit_status_callback(self.state)

        # 1. Lower Arm
        for i in range(140, 90, -1):
            self.servos.set_angle("arm_lift", i)
            await asyncio.sleep(0.01)
        
        # 2. Open Claw
        for i in range(90, 130, 1): # Original 130 was closed? Wait, fix map.
            # Fixed map: Claw 90 is Open, 140 is Closed.
            # Drop: Lower (to 90), Open (to 90)
            self.servos.set_angle("claw", 90) # Open
            await asyncio.sleep(0.01)

        # 3. Lift Arm back up
        for i in range(90, 140, 1):
            self.servos.set_angle("arm_lift", i)
            await asyncio.sleep(0.01)
            
        self.state["status"] = "standby"
        if self.emit_status_callback: await self.emit_status_callback(self.state)

    async def _auto_pickup_sequence(self):
        print("Starting auto pickup sequence...")
        self.state["status"] = "pickup_approach"
        if self.emit_status_callback: await self.emit_status_callback(self.state)
        
        try:
            # 1. Approach object using Ultrasonic
            while True:
                # CLIFF CHECK
                if self._check_cliff():
                    print("Cliff detected during pickup! Stopping.")
                    self.motors.stop()
                    break

                distances = self.ultrasonic.get_distances()
                dist = distances.get("front")
                
                if dist is None or dist == 0:
                    await asyncio.sleep(0.1)
                    continue
                
                if dist <= 5:
                    self.motors.move(0, -0.4) # Backup slowly
                elif dist > 5 and dist < 7.5:
                     self.motors.move(0, -0.3) # Backup very slowly
                elif dist >= 7.5 and dist <= 8.5:
                     self.motors.stop()
                     break # In position
                elif dist > 8.5 and dist < 15:
                     self.motors.move(0, 0.3) # Forward slowly
                elif dist >= 15:
                     self.motors.move(0, 0.5) # Forward
                     
                await asyncio.sleep(0.1)
            
            self.motors.stop()
            self.state["status"] = "pickup_lifting"
            if self.emit_status_callback: await self.emit_status_callback(self.state)
            
            # 2. Lift Sequence
            # Fixed Servo Logic:
            # Lift: 140 (Up) -> 90 (Down)
            # Claw: 90 (Open) -> 140 (Closed)
            
            self.servos.set_angle("claw", 90) # Open
            await asyncio.sleep(0.5)
            
            self.servos.set_angle("arm_lift", 90) # Down
            await asyncio.sleep(0.5)
            
            # Close Claw
            for i in range(90, 140, 1):
                self.servos.set_angle("claw", i) 
                await asyncio.sleep(0.01)
                
            await asyncio.sleep(0.5)
            
            # Lift Arm
            for i in range(90, 140, 1):
                self.servos.set_angle("arm_lift", i) 
                await asyncio.sleep(0.01)
                
            print("Pickup complete")
            self.state["status"] = "holding"
            if self.emit_status_callback: await self.emit_status_callback(self.state)

        except asyncio.CancelledError:
            print("Pickup sequence cancelled")
            self.motors.stop()
            self.state["status"] = "standby"
        except Exception as e:
            print(f"Pickup error: {e}")
            self.motors.stop()
            self.state["status"] = "error"

    async def _track_face_loop(self):
        print("Starting face tracking...")
        self.state["status"] = "tracking_face"
        self.leds.set_mode("blink", (0, 0, 255)) # Blink Blue
        if self.emit_status_callback: await self.emit_status_callback(self.state)
        
        try:
            while True:
                # CLIFF CHECK
                if self._check_cliff():
                    print("Cliff detected during face tracking! Stopping.")
                    self.motors.stop()
                    await asyncio.sleep(0.5)
                    # Back up a bit?
                    self.motors.move(0, -0.3)
                    await asyncio.sleep(0.5)
                    self.motors.stop()
                    continue

                frame = self.camera_manager.get_latest_frame('front')
                if frame is None:
                    await asyncio.sleep(0.1)
                    continue
                
                _, detections = self.ai_service.process_frame(frame)
                target = next((d for d in detections if d['label'] == 'person'), None)
                
                if target:
                    bbox = target['bbox']
                    center_x = (bbox[0] + bbox[2]) / 2
                    frame_width = frame.shape[1]
                    offset_x = (center_x - frame_width / 2) / (frame_width / 2)
                    
                    if abs(offset_x) < 0.2:
                        self.motors.move(0, 0)
                    else:
                        turn_speed = offset_x * 0.5
                        self.motors.move(turn_speed, 0)
                else:
                    self.motors.stop()
                
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            print("Tracking cancelled")
            self.motors.stop()
            self.leds.set_mode("static", (0, 255, 0)) # Back to Green
            self.state["status"] = "standby"
        except Exception as e:
            self.motors.stop()

    async def _line_tracking_loop(self):
        print("Starting line tracking...")
        self.state["status"] = "line_tracking"
        self.leds.set_mode("static", (255, 255, 0)) # Yellow
        if self.emit_status_callback: await self.emit_status_callback(self.state)
        
        try:
            while True:
                # Logic from infrared.py / car.py
                ir_val = self.infrared.read_all_infrared_byte()
                
                # Using somewhat standardized move params
                if ir_val == 2: # 010 - Forward
                    self.motors.move(0, 0.4)
                elif ir_val == 4: # 100 - Left
                    self.motors.move(-0.4, 0.2)
                elif ir_val == 1: # 001 - Right
                    self.motors.move(0.4, 0.2)
                elif ir_val == 6: # 110 - Sharp Left
                    self.motors.move(-0.6, 0.1)
                elif ir_val == 3: # 011 - Sharp Right
                    self.motors.move(0.6, 0.1)
                elif ir_val == 7: # 111 - Stop (All Black/Line)
                    self.motors.move(0, 0)
                else:
                    self.motors.move(0, 0)
                    
                await asyncio.sleep(0.05)
                
        except asyncio.CancelledError:
            print("Line tracking cancelled")
            self.motors.stop()
            self.leds.set_mode("static", (0, 255, 0))
            self.state["status"] = "standby"

    async def _obstacle_avoidance_loop(self):
        print("Starting smart obstacle avoidance...")
        self.state["status"] = "obstacle_avoidance"
        self.leds.set_mode("static", (255, 0, 0)) # Red
        if self.emit_status_callback: await self.emit_status_callback(self.state)
        
        try:
            while True:
                # CLIFF CHECK
                if self._check_cliff():
                    print("Cliff detected! Backing up from edge.")
                    self.motors.stop()
                    await asyncio.sleep(0.2)
                    self.motors.move(0, -0.3)
                    await asyncio.sleep(0.5)
                    self.motors.move(0.5, 0) # Spin away
                    await asyncio.sleep(0.5)
                    continue

                distances = self.ultrasonic.get_distances()
                front_dist = distances.get("front", 0)
                rear_dist = distances.get("rear", 0)
                
                # Default slow speed
                speed = 0.25
                
                if front_dist and front_dist < 40:
                    # SLOW DOWN ZONE
                    speed = 0.15
                    
                    if front_dist < 20:
                        # CRITICAL ZONE - STOP AND THINK
                        print(f"Obstacle detected at {front_dist}cm. Stopping.")
                        self.motors.stop()
                        await asyncio.sleep(0.5)
                        
                        # Check Rear for backing up space
                        can_backup = rear_dist and rear_dist > 30
                        
                        # Scan Left (Turn Left briefly)
                        self.motors.move(-0.3, 0.3) # Rotate Left
                        await asyncio.sleep(0.4)
                        self.motors.stop()
                        await asyncio.sleep(0.2)
                        distances = self.ultrasonic.get_distances()
                        left_space = distances.get("front", 0)
                        
                        # Scan Right (Turn Right past center)
                        self.motors.move(0.3, 0.3) # Rotate Right
                        await asyncio.sleep(0.8) # Double time to go right
                        self.motors.stop()
                        await asyncio.sleep(0.2)
                        distances = self.ultrasonic.get_distances()
                        right_space = distances.get("front", 0)
                        
                        # Re-center (roughly)
                        self.motors.move(-0.3, 0.3) # Rotate Left back to center
                        await asyncio.sleep(0.4)
                        self.motors.stop()
                        
                        print(f"Scan Result: Left={left_space}, Right={right_space}")
                        
                        # Decision
                        if left_space > 25 and left_space > right_space:
                            # Turn Left
                            print("Turning Left")
                            self.motors.move(-0.4, 0.3)
                            await asyncio.sleep(0.6)
                        elif right_space > 25:
                            # Turn Right
                            print("Turning Right")
                            self.motors.move(0.4, 0.3)
                            await asyncio.sleep(0.6)
                        else:
                            # Trapped or Wall -> Back up and Spin
                            print("Path blocked. Backing up.")
                            if can_backup:
                                self.motors.move(0, -0.25)
                                await asyncio.sleep(0.8)
                            
                            # Spin 180 (approx)
                            self.motors.move(0.5, 0) # Rotate in place
                            await asyncio.sleep(0.8)
                            
                        continue # Restart loop
                
                # Move Forward
                self.motors.move(0, speed)
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            print("Obstacle avoidance cancelled")
            self.motors.stop()
            self.leds.set_mode("static", (0, 255, 0))
            self.state["status"] = "standby"

    async def _stop_movement(self):
        print("Stopping all movement")
        self.motors.stop()
        await self._cancel_tasks()
        self.state["status"] = "standby"
        if self.emit_status_callback:
            await self.emit_status_callback(self.state)
        
    async def _sensor_loop(self):
        """Updates sensor data periodically"""
        while self.is_running:
            # Update Ultrasonic
            self.state["sensors"]["ultrasonic"] = self.ultrasonic.get_distances()
            self.state["sensors"]["infrared"] = self.infrared.get_values()
            
            # Simulate battery drain or read from ADC if implemented
            self.state["battery"] = max(0, self.state["battery"] - 0.001)
            
            if self.emit_status_callback:
                await self.emit_status_callback(self.state)
                
            await asyncio.sleep(0.5) # Update rate 2Hz

# Global Robot Instance
robot = Robot()
