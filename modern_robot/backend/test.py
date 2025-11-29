#!/usr/bin/env python3
"""
Test script for Modern Robot hardware functions
Tests motors, servos, camera, and robot control commands
"""

import asyncio
import time
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.robot import robot, AutonomyLevel
from app.core.hardware.motors import MotorController
from app.core.hardware.servos import ServoController
from app.core.hardware.camera import CameraManager
from app.core.config import settings

class RobotTester:
    def __init__(self):
        self.passed_tests = 0
        self.failed_tests = 0
        self.robot = robot

    def log(self, message, level="INFO"):
        """Print formatted log message"""
        colors = {
            "INFO": "\033[94m",
            "SUCCESS": "\033[92m",
            "ERROR": "\033[91m",
            "WARNING": "\033[93m"
        }
        reset = "\033[0m"
        print(f"{colors.get(level, '')}{level}: {message}{reset}")

    def test_result(self, test_name, success, message=""):
        """Record test result"""
        if success:
            self.passed_tests += 1
            self.log(f"✓ {test_name} PASSED {message}", "SUCCESS")
        else:
            self.failed_tests += 1
            self.log(f"✗ {test_name} FAILED {message}", "ERROR")

    def print_separator(self, title=""):
        """Print section separator"""
        print("\n" + "="*60)
        if title:
            print(f"  {title}")
            print("="*60)

    # ===================== Motor Tests =====================

    async def test_motors_initialization(self):
        """Test motor controller initialization"""
        self.print_separator("MOTOR TESTS")
        try:
            motor_controller = MotorController()
            success = motor_controller is not None
            self.test_result("Motor Initialization", success)
            return motor_controller
        except Exception as e:
            self.test_result("Motor Initialization", False, f"- {str(e)}")
            return None

    async def test_motor_forward(self, duration=2):
        """Test forward movement"""
        try:
            self.log("Testing forward movement...")
            self.robot.motors.move(0, 0.5)
            await asyncio.sleep(duration)
            self.robot.motors.stop()
            self.test_result("Motor Forward", True)
        except Exception as e:
            self.test_result("Motor Forward", False, f"- {str(e)}")

    async def test_motor_backward(self, duration=2):
        """Test backward movement"""
        try:
            self.log("Testing backward movement...")
            self.robot.motors.move(0, -0.5)
            await asyncio.sleep(duration)
            self.robot.motors.stop()
            self.test_result("Motor Backward", True)
        except Exception as e:
            self.test_result("Motor Backward", False, f"- {str(e)}")

    async def test_motor_turn_left(self, duration=2):
        """Test left turn"""
        try:
            self.log("Testing left turn...")
            self.robot.motors.move(-0.5, 0)
            await asyncio.sleep(duration)
            self.robot.motors.stop()
            self.test_result("Motor Turn Left", True)
        except Exception as e:
            self.test_result("Motor Turn Left", False, f"- {str(e)}")

    async def test_motor_turn_right(self, duration=2):
        """Test right turn"""
        try:
            self.log("Testing right turn...")
            self.robot.motors.move(0.5, 0)
            await asyncio.sleep(duration)
            self.robot.motors.stop()
            self.test_result("Motor Turn Right", True)
        except Exception as e:
            self.test_result("Motor Turn Right", False, f"- {str(e)}")

    async def test_motor_stop(self):
        """Test motor stop"""
        try:
            self.log("Testing motor stop...")
            self.robot.motors.move(0.5, 0.5)
            await asyncio.sleep(0.5)
            self.robot.motors.stop()
            self.test_result("Motor Stop", True)
        except Exception as e:
            self.test_result("Motor Stop", False, f"- {str(e)}")

    # ===================== Servo Tests =====================

    async def test_servos_initialization(self):
        """Test servo controller initialization"""
        self.print_separator("SERVO TESTS")
        try:
            servo_controller = ServoController()
            success = servo_controller is not None
            self.test_result("Servo Initialization", success)
            return servo_controller
        except Exception as e:
            self.test_result("Servo Initialization", False, f"- {str(e)}")
            return None

    async def test_servo_arm_lift(self):
        """Test arm lift servo"""
        try:
            self.log("Testing arm lift servo (0° -> 90° -> 180°)...")
            for angle in [0, 90, 180]:
                self.robot.servos.set_angle("arm_lift", angle)
                self.log(f"  Arm lift: {angle}°")
                await asyncio.sleep(1)
            self.test_result("Servo Arm Lift", True)
        except Exception as e:
            self.test_result("Servo Arm Lift", False, f"- {str(e)}")

    async def test_servo_claw(self):
        """Test claw servo"""
        try:
            self.log("Testing claw servo (open/close)...")
            # Close claw
            self.robot.servos.set_angle("claw", 0)
            self.log("  Claw: closed (0°)")
            await asyncio.sleep(1)
            # Open claw
            self.robot.servos.set_angle("claw", 90)
            self.log("  Claw: open (90°)")
            await asyncio.sleep(1)
            self.test_result("Servo Claw", True)
        except Exception as e:
            self.test_result("Servo Claw", False, f"- {str(e)}")

    async def test_servo_camera_pan(self):
        """Test rear camera pan servo"""
        try:
            self.log("Testing camera pan servo (left/center/right)...")
            positions = {"left": 0, "center": 90, "right": 180}
            for name, angle in positions.items():
                self.robot.servos.set_angle("rear_cam", angle)
                self.log(f"  Camera: {name} ({angle}°)")
                await asyncio.sleep(1)
            self.test_result("Servo Camera Pan", True)
        except Exception as e:
            self.test_result("Servo Camera Pan", False, f"- {str(e)}")

    # ===================== Camera Tests =====================

    async def test_camera_initialization(self):
        """Test camera manager initialization"""
        self.print_separator("CAMERA TESTS")
        try:
            camera_manager = CameraManager()
            camera_manager.start()
            success = camera_manager is not None
            self.test_result("Camera Initialization", success)
            await asyncio.sleep(1)
            return camera_manager
        except Exception as e:
            self.test_result("Camera Initialization", False, f"- {str(e)}")
            return None

    async def test_camera_front_capture(self):
        """Test front camera frame capture"""
        import cv2
        try:
            self.log("Testing front camera capture...")
            self.log("Displaying front camera window (press 'q' to close or wait 5 seconds)...")

            # Show camera feed for 5 seconds
            start_time = time.time()
            success = False

            while time.time() - start_time < 5:
                frame_bytes = self.robot.camera_manager.front_cam.get_frame()
                if frame_bytes:
                    success = True
                    # Decode JPEG bytes to image
                    import numpy as np
                    nparr = np.frombuffer(frame_bytes, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                    if frame is not None:
                        # Add timestamp and info
                        cv2.putText(frame, "Front Camera", (10, 30),
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        cv2.putText(frame, f"Time: {time.time() - start_time:.1f}s", (10, 60),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

                        cv2.imshow("Front Camera Test", frame)

                        # Break if 'q' is pressed
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break

                await asyncio.sleep(0.03)  # ~30 FPS

            cv2.destroyWindow("Front Camera Test")
            self.test_result("Front Camera Capture", success,
                           f"- Frame size: {len(frame_bytes) if frame_bytes else 0} bytes")
        except Exception as e:
            cv2.destroyAllWindows()
            self.test_result("Front Camera Capture", False, f"- {str(e)}")

    async def test_camera_rear_capture(self):
        """Test rear camera frame capture"""
        import cv2
        try:
            self.log("Testing rear camera capture...")
            self.log("Displaying rear camera window (press 'q' to close or wait 5 seconds)...")

            # Show camera feed for 5 seconds
            start_time = time.time()
            success = False

            while time.time() - start_time < 5:
                frame_bytes = self.robot.camera_manager.rear_cam.get_frame()
                if frame_bytes:
                    success = True
                    # Decode JPEG bytes to image
                    import numpy as np
                    nparr = np.frombuffer(frame_bytes, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                    if frame is not None:
                        # Add timestamp and info
                        cv2.putText(frame, "Rear Camera", (10, 30),
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        cv2.putText(frame, f"Time: {time.time() - start_time:.1f}s", (10, 60),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

                        cv2.imshow("Rear Camera Test", frame)

                        # Break if 'q' is pressed
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break

                await asyncio.sleep(0.03)  # ~30 FPS

            cv2.destroyWindow("Rear Camera Test")
            self.test_result("Rear Camera Capture", success,
                           f"- Frame size: {len(frame_bytes) if frame_bytes else 0} bytes")
        except Exception as e:
            cv2.destroyAllWindows()
            self.test_result("Rear Camera Capture", False, f"- {str(e)}")

    async def test_both_cameras_simultaneous(self):
        """Test both cameras simultaneously"""
        import cv2
        try:
            self.log("Testing both cameras simultaneously...")
            self.log("Displaying both camera windows (press 'q' to close or wait 10 seconds)...")

            # Show both camera feeds for 10 seconds
            start_time = time.time()
            front_success = False
            rear_success = False

            while time.time() - start_time < 10:
                # Front camera
                front_bytes = self.robot.camera_manager.front_cam.get_frame()
                if front_bytes:
                    front_success = True
                    import numpy as np
                    nparr = np.frombuffer(front_bytes, np.uint8)
                    front_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                    if front_frame is not None:
                        cv2.putText(front_frame, "Front Camera", (10, 30),
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        cv2.putText(front_frame, f"Time: {time.time() - start_time:.1f}s", (10, 60),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
                        cv2.imshow("Front Camera", front_frame)

                # Rear camera
                rear_bytes = self.robot.camera_manager.rear_cam.get_frame()
                if rear_bytes:
                    rear_success = True
                    import numpy as np
                    nparr = np.frombuffer(rear_bytes, np.uint8)
                    rear_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                    if rear_frame is not None:
                        cv2.putText(rear_frame, "Rear Camera", (10, 30),
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        cv2.putText(rear_frame, f"Time: {time.time() - start_time:.1f}s", (10, 60),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
                        cv2.imshow("Rear Camera", rear_frame)

                # Break if 'q' is pressed
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                await asyncio.sleep(0.03)  # ~30 FPS

            cv2.destroyAllWindows()
            success = front_success and rear_success
            self.test_result("Both Cameras Simultaneous", success,
                           f"- Front: {'OK' if front_success else 'FAILED'}, Rear: {'OK' if rear_success else 'FAILED'}")
        except Exception as e:
            cv2.destroyAllWindows()
            self.test_result("Both Cameras Simultaneous", False, f"- {str(e)}")

    # ===================== Robot Command Tests =====================

    async def test_robot_commands(self):
        """Test robot command execution"""
        self.print_separator("ROBOT COMMAND TESTS")

        # Test move command
        try:
            self.log("Testing move command...")
            await self.robot.execute_command({
                'command': 'move',
                'params': {'x': 0.3, 'y': 0.3}
            })
            await asyncio.sleep(1)
            await self.robot.execute_command({
                'command': 'move',
                'params': {'x': 0, 'y': 0}
            })
            self.test_result("Robot Move Command", True)
        except Exception as e:
            self.test_result("Robot Move Command", False, f"- {str(e)}")

        # Test camera pan command
        try:
            self.log("Testing camera pan command...")
            await self.robot.execute_command({
                'command': 'camera_pan',
                'params': {'angle': 90}
            })
            await asyncio.sleep(1)
            self.test_result("Robot Camera Pan Command", True)
        except Exception as e:
            self.test_result("Robot Camera Pan Command", False, f"- {str(e)}")

        # Test arm control command
        try:
            self.log("Testing arm control command...")
            await self.robot.execute_command({
                'command': 'arm_control',
                'params': {'joint': 'lift', 'value': 90}
            })
            await asyncio.sleep(1)
            await self.robot.execute_command({
                'command': 'arm_control',
                'params': {'joint': 'claw', 'value': 45}
            })
            await asyncio.sleep(1)
            self.test_result("Robot Arm Control Command", True)
        except Exception as e:
            self.test_result("Robot Arm Control Command", False, f"- {str(e)}")

    # ===================== Autonomy Tests =====================

    async def test_autonomy_levels(self):
        """Test autonomy level switching"""
        self.print_separator("AUTONOMY LEVEL TESTS")

        levels = [AutonomyLevel.MANUAL, AutonomyLevel.SEMI_AUTO, AutonomyLevel.FULL_AUTO]
        try:
            for level in levels:
                self.log(f"Setting autonomy level to: {level.value}")
                self.robot.set_autonomy_level(level.value)
                current_level = self.robot.state["autonomy_level"]
                success = current_level == level.value
                self.test_result(f"Autonomy Level: {level.value}", success)
                await asyncio.sleep(0.5)
        except Exception as e:
            self.test_result("Autonomy Level Switching", False, f"- {str(e)}")

    # ===================== State Tests =====================

    async def test_robot_state(self):
        """Test robot state retrieval"""
        self.print_separator("ROBOT STATE TESTS")
        try:
            state = self.robot.get_state()
            success = isinstance(state, dict) and "autonomy_level" in state
            self.test_result("Robot State Retrieval", success)
            if success:
                self.log(f"Current state: {state}", "INFO")
        except Exception as e:
            self.test_result("Robot State Retrieval", False, f"- {str(e)}")

    # ===================== Emergency Stop Test =====================

    async def test_emergency_stop(self):
        """Test emergency stop functionality"""
        self.print_separator("EMERGENCY STOP TEST")
        try:
            self.log("Testing emergency stop...")
            # Start movement
            self.robot.motors.move(0.5, 0.5)
            await asyncio.sleep(0.5)
            # Emergency stop
            await self.robot.execute_command({'command': 'emergency_stop'})
            self.test_result("Emergency Stop", True)
        except Exception as e:
            self.test_result("Emergency Stop", False, f"- {str(e)}")

    # ===================== Integration Tests =====================

    async def test_full_sequence(self):
        """Test a full sequence of robot movements"""
        self.print_separator("FULL SEQUENCE TEST")
        try:
            self.log("Executing full movement sequence...")

            # Move forward
            self.log("  1. Moving forward...")
            await self.robot.execute_command({'command': 'move', 'params': {'x': 0, 'y': 0.4}})
            await asyncio.sleep(1)

            # Turn left
            self.log("  2. Turning left...")
            await self.robot.execute_command({'command': 'move', 'params': {'x': -0.4, 'y': 0}})
            await asyncio.sleep(1)

            # Stop
            self.log("  3. Stopping...")
            await self.robot.execute_command({'command': 'move', 'params': {'x': 0, 'y': 0}})
            await asyncio.sleep(0.5)

            # Pan camera
            self.log("  4. Panning camera...")
            await self.robot.execute_command({'command': 'camera_pan', 'params': {'angle': 135}})
            await asyncio.sleep(1)

            # Move arm
            self.log("  5. Moving arm...")
            await self.robot.execute_command({'command': 'arm_control', 'params': {'joint': 'lift', 'value': 120}})
            await asyncio.sleep(1)

            # Open claw
            self.log("  6. Opening claw...")
            await self.robot.execute_command({'command': 'arm_control', 'params': {'joint': 'claw', 'value': 90}})
            await asyncio.sleep(1)

            self.test_result("Full Sequence Test", True)
        except Exception as e:
            self.test_result("Full Sequence Test", False, f"- {str(e)}")

    # ===================== Main Test Runner =====================

    async def run_all_tests(self, quick_mode=False):
        """Run all tests"""
        self.print_separator("STARTING ROBOT HARDWARE TESTS")
        self.log(f"Mode: {'MOCK' if settings.MOCK_MODE else 'REAL HARDWARE'}", "WARNING")
        self.log(f"Quick Mode: {'Enabled' if quick_mode else 'Disabled'}", "INFO")

        # Initialize robot
        await self.robot.start()
        await asyncio.sleep(1)

        # Test duration (shorter in quick mode)
        test_duration = 1 if quick_mode else 2

        # Run tests
        await self.test_motors_initialization()
        await self.test_motor_forward(test_duration)
        await self.test_motor_backward(test_duration)
        await self.test_motor_turn_left(test_duration)
        await self.test_motor_turn_right(test_duration)
        await self.test_motor_stop()

        await self.test_servos_initialization()
        await self.test_servo_arm_lift()
        await self.test_servo_claw()
        await self.test_servo_camera_pan()

        await self.test_camera_initialization()
        await self.test_camera_front_capture()
        await self.test_camera_rear_capture()
        if not quick_mode:
            await self.test_both_cameras_simultaneous()

        await self.test_robot_commands()
        await self.test_autonomy_levels()
        await self.test_robot_state()
        await self.test_emergency_stop()

        if not quick_mode:
            await self.test_full_sequence()

        # Cleanup
        await self.robot.stop()

        # Print summary
        self.print_test_summary()

    def print_test_summary(self):
        """Print test results summary"""
        self.print_separator("TEST SUMMARY")
        total_tests = self.passed_tests + self.failed_tests
        success_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print("="*60 + "\n")

        if self.failed_tests == 0:
            self.log("All tests passed!", "SUCCESS")
        else:
            self.log(f"{self.failed_tests} test(s) failed", "ERROR")

# ===================== CLI Interface =====================

async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Test Modern Robot Hardware Functions")
    parser.add_argument('--quick', action='store_true', help='Run tests in quick mode (shorter durations)')
    parser.add_argument('--mock', action='store_true', help='Force MOCK mode')
    parser.add_argument('--test', type=str, help='Run specific test (motor, servo, camera, command, autonomy, state)')

    args = parser.parse_args()

    # Override mock mode if specified
    if args.mock:
        os.environ["MOCK_MODE"] = "true"
        settings.MOCK_MODE = True

    tester = RobotTester()

    if args.test:
        # Run specific test category
        test_map = {
            'motor': [
                tester.test_motors_initialization,
                tester.test_motor_forward,
                tester.test_motor_backward,
                tester.test_motor_turn_left,
                tester.test_motor_turn_right,
                tester.test_motor_stop
            ],
            'servo': [
                tester.test_servos_initialization,
                tester.test_servo_arm_lift,
                tester.test_servo_claw,
                tester.test_servo_camera_pan
            ],
            'camera': [
                tester.test_camera_initialization,
                tester.test_camera_front_capture,
                tester.test_camera_rear_capture,
                tester.test_both_cameras_simultaneous
            ],
            'command': [tester.test_robot_commands],
            'autonomy': [tester.test_autonomy_levels],
            'state': [tester.test_robot_state]
        }

        if args.test in test_map:
            await robot.start()
            tester.print_separator(f"RUNNING {args.test.upper()} TESTS")
            for test_func in test_map[args.test]:
                await test_func()
            await robot.stop()
            tester.print_test_summary()
        else:
            print(f"Unknown test category: {args.test}")
            print(f"Available categories: {', '.join(test_map.keys())}")
    else:
        # Run all tests
        await tester.run_all_tests(quick_mode=args.quick)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
