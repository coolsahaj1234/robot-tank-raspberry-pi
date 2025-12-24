#!/usr/bin/env python3
"""
Headless Server for Robot Tank
Runs without GUI - suitable for SSH/headless operation
"""
import sys
import struct
import time
import signal
import threading
import multiprocessing
from server import TankServer
from message import MessageParser
from command import Command
from led import Led
from camera import Camera
from car import Car

class HeadlessServer:
    def __init__(self):
        print("Initializing Headless Robot Tank Server...")
        
        # Initialize components
        self.tcp_server = TankServer()
        self.command = Command()
        self.led = Led()
        self.car = Car()
        self.camera = Camera(stream_size=(400, 300))
        self.queue_cmd = multiprocessing.Queue()
        self.cmd_parser = MessageParser()
        self.queue_led = multiprocessing.Queue()
        self.led_parser = MessageParser()
        # Shared value to track connection status for LED process
        self.connection_status = multiprocessing.Value('i', 0)  # 0 = disconnected, 1 = connected
        
        # Thread/process flags
        self.cmd_thread = None
        self.video_thread = None
        self.car_thread = None
        self.led_process = None
        self.cmd_thread_is_running = False
        self.video_thread_is_running = False
        self.car_thread_is_running = False
        self.led_process_is_running = False
        
        # Car state
        self.car_mode = 1  # Default to mode 1 (manual control)
        self.car_last_mode = 1
        self.left_wheel_speed = 0
        self.right_wheel_speed = 0
        
        # Setup signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("Server initialized successfully!")

    def start(self):
        """Start all server components"""
        print("Starting TCP servers on ports 5003 (commands) and 8003 (video)...")
        self.tcp_server.startTcpServer(5003, 8003)
        print(f"Server listening on {self.tcp_server.ip}:5003 (commands) and {self.tcp_server.ip}:8003 (video)")
        
        # Initialize servos to starting positions
        print("Resetting servos to starting positions...")
        self.car.servo.setServoAngle('0', 90)   # Servo 0 to 90 degrees
        self.car.servo.setServoAngle('1', 140)  # Servo 1 to 140 degrees
        time.sleep(0.5)  # Give servos time to move to position
        print("Servos reset to starting positions (Servo 0: 90°, Servo 1: 140°)")
        
        # Start all threads and processes
        self.set_threading_cmd_receive(True)
        self.set_threading_video_send(True)
        self.set_threading_car_task(True)
        self.set_process_led_running(True)
        
        # Start LED breathing mode (red color: 255, 0, 0) - no connection initially
        # Format: CMD_LED#mode#R#G#B#index
        print("Starting LED breathing mode (red - waiting for connection)...")
        self.queue_led.put("CMD_LED#4#255#0#0#0")
        time.sleep(0.3)  # Give LED process time to start
        
        # Start connection monitoring thread (after LED process is running)
        self.connection_monitor_running = True
        self.connection_monitor_thread = threading.Thread(target=self.threading_connection_monitor, daemon=True)
        self.connection_monitor_thread.start()
        print("Connection monitor thread started")
        
        print("Server started! Waiting for client connections...")
        print("LED Status: Red = No connection, Blue = Client connected")
        print("Press Ctrl+C to stop the server")

    def stop(self):
        """Stop all server components"""
        print("\nStopping server...")
        # Stop connection monitor
        self.connection_monitor_running = False
        if hasattr(self, 'connection_monitor_thread') and self.connection_monitor_thread:
            self.connection_monitor_thread.join(0.5)
        self.set_threading_cmd_receive(False)
        self.set_threading_video_send(False)
        self.set_threading_car_task(False)
        self.set_process_led_running(False)
        if self.tcp_server:
            self.tcp_server.stopTcpServer()
        # Stop car and cleanup
        try:
            self.led.colorWipe([0, 0, 0])
        except:
            pass
        try:
            self.camera.stop_stream()
            self.camera.close()
        except:
            pass
        try:
            self.car.close()
        except:
            pass
        print("Server stopped.")

    def signal_handler(self, signal, frame):
        """Handle Ctrl+C gracefully"""
        self.stop()
        sys.exit(0)

    def set_threading_cmd_receive(self, state):
        """Start or stop command receive thread"""
        if state and not self.cmd_thread_is_running:
            self.cmd_thread_is_running = True
            self.cmd_thread = threading.Thread(target=self.threading_cmd_receive, daemon=True)
            self.cmd_thread.start()
            print("Command receive thread started")
        elif not state and self.cmd_thread_is_running:
            self.cmd_thread_is_running = False
            if self.cmd_thread:
                self.cmd_thread.join(0.5)
            print("Command receive thread stopped")

    def threading_cmd_receive(self):
        """Thread that receives and processes commands from clients"""
        while self.cmd_thread_is_running:
            try:
                cmd_queue = self.tcp_server.readDataFromCmdServer()
                if cmd_queue.qsize() > 0:
                    client_address, all_message = cmd_queue.get()
                    main_message = all_message.strip()
                    
                    # Handle multiple commands separated by newlines
                    if "\n" in main_message:
                        for msg in main_message.split("\n"):
                            if msg.strip():
                                self.queue_cmd.put(msg.strip())
                    else:
                        if main_message:
                            self.queue_cmd.put(main_message)
                
                # Process commands from queue
                while not self.queue_cmd.empty():
                    msg = self.queue_cmd.get()
                    self.cmd_parser.clearParameters()
                    self.cmd_parser.parser(msg)
                    
                    # Print received command for debugging
                    print(f"{msg}")
                    
                    # Handle LED commands
                    if self.cmd_parser.commandString == self.command.CMD_LED:
                        self.queue_led.put(msg)
                    
                    # Handle motor commands
                    elif self.cmd_parser.commandString == self.command.CMD_MOTOR:
                        self.left_wheel_speed = int(self.cmd_parser.intParameter[0])
                        self.right_wheel_speed = int(self.cmd_parser.intParameter[1])
                        self.car.motor.setMotorModel(self.left_wheel_speed, self.right_wheel_speed)
                    
                    # Handle servo commands - now uses smooth interpolation (fast response, smooth movement)
                    elif self.cmd_parser.commandString == self.command.CMD_SERVO:
                        if self.car_mode == 1 or self.car_mode == 2:
                            servo_index = int(self.cmd_parser.intParameter[0])
                            servo_angle = int(self.cmd_parser.intParameter[1])
                            # Set target angle immediately - smooth interpolation happens in background thread
                            self.car.servo.setServoAngle(servo_index, servo_angle)
                        else:
                            print("You can control the servo only in Move mode and Sonar mode")
                    
                    # Handle mode commands
                    elif self.cmd_parser.commandString == self.command.CMD_MODE:
                        if self.car.infrared_run_stop == False:
                            self.car.infrared_run_stop = True
                            time.sleep(0.1)
                        mode = int(self.cmd_parser.intParameter[0])
                        if mode == 0:
                            self.car_mode = 1
                            self.left_wheel_speed = 0
                            self.right_wheel_speed = 0
                            self.car.motor.setMotorModel(0, 0)
                        elif mode == 1:
                            self.car_mode = 2
                        elif mode == 2:
                            self.car_mode = 3
                            self.car.infrared_run_stop = False
                        self.car_last_mode = self.car_mode
                        print(f"Mode changed to: {self.car_mode}")
                    
                    # Handle action commands
                    elif self.cmd_parser.commandString == self.command.CMD_ACTION:
                        if self.car.infrared_run_stop == False:
                            self.car.infrared_run_stop = True
                            time.sleep(0.1)
                        action = int(self.cmd_parser.intParameter[0])
                        if action == 0:
                            self.car_mode = 4
                        elif action == 1:
                            self.car_mode = 5
                        elif action == 2:
                            self.car_mode = 6
                
                if self.queue_cmd.empty():
                    time.sleep(0.001)
            except Exception as e:
                print(f"Error in command receive thread: {e}")
                time.sleep(0.1)

    def set_threading_car_task(self, state):
        """Start or stop car task thread"""
        if state and not self.car_thread_is_running:
            self.car_thread_is_running = True
            self.car_thread = threading.Thread(target=self.threading_car_task, daemon=True)
            self.car_thread.start()
            print("Car task thread started")
        elif not state and self.car_thread_is_running:
            self.car_thread_is_running = False
            if self.car_thread:
                self.car_thread.join(0.5)
            print("Car task thread stopped")

    def threading_car_task(self):
        """Thread that handles autonomous car modes"""
        while self.car_thread_is_running:
            try:
                if self.car_mode == 1:
                    # Manual mode - send both front and back ultrasonic distances
                    distance_front = self.car.sonic.get_distance()
                    distance_back = self.car.sonic_back.get_distance()
                    if self.tcp_server.get_cmd_server_busy() == False:
                        self.tcp_server.set_cmd_server_busy(True)
                        self.tcp_server.sendDataToCmdClinet(f"CMD_SONIC#{distance_front:.2f}#{distance_back:.2f}")
                        self.tcp_server.set_cmd_server_busy(False)
                    time.sleep(1)
                elif self.car_mode == 2:
                    # Ultrasonic obstacle avoidance mode
                    self.car.mode_ultrasonic()
                    distance_front = self.car.sonic.get_distance()
                    distance_back = self.car.sonic_back.get_distance()
                    if self.tcp_server.get_cmd_server_busy() == False:
                        self.tcp_server.set_cmd_server_busy(True)
                        self.tcp_server.sendDataToCmdClinet(f"CMD_SONIC#{distance_front:.2f}#{distance_back:.2f}")
                        self.tcp_server.set_cmd_server_busy(False)
                elif self.car_mode == 3:
                    # Infrared line following mode
                    self.car.mode_infrared()
                elif self.car_mode == 4:
                    # Clamp stop
                    self.car.mode_clamp(0)
                    self.car_mode = self.car_last_mode
                    self.tcp_server.sendDataToCmdClinet("CMD_ACTION#0\r\n")
                    print("clamp stop...")
                elif self.car_mode == 5:
                    # Clamp up
                    self.car.set_mode_clamp(1)
                    while self.car_thread_is_running and self.car_mode == 5:
                        if self.car.get_mode_clamp() == 1:
                            self.car.mode_clamp()
                            print("clamp up...")
                        elif self.car.get_mode_clamp() == 0:
                            self.car_mode = self.car_last_mode
                            self.tcp_server.sendDataToCmdClinet("CMD_ACTION#10\r\n")
                            print("clamp up stop")
                            break
                elif self.car_mode == 6:
                    # Clamp down
                    self.car.set_mode_clamp(2)
                    while self.car_thread_is_running and self.car_mode == 6:
                        if self.car.get_mode_clamp() == 2:
                            self.car.mode_clamp()
                            print("clamp down...")
                        elif self.car.get_mode_clamp() == 0:
                            self.car_mode = self.car_last_mode
                            self.tcp_server.sendDataToCmdClinet("CMD_ACTION#20\r\n")
                            print("clamp down stop")
                            break
                time.sleep(0.01)
            except Exception as e:
                print(f"Error in car task thread: {e}")
                time.sleep(0.1)

    def set_threading_video_send(self, state):
        """Start or stop video send thread"""
        if state and not self.video_thread_is_running:
            self.video_thread_is_running = True
            self.video_thread = threading.Thread(target=self.threading_video_send, daemon=True)
            self.video_thread.start()
            print("Video send thread started")
        elif not state and self.video_thread_is_running:
            self.video_thread_is_running = False
            if self.video_thread:
                self.video_thread.join(0.5)
            print("Video send thread stopped")

    def threading_video_send(self):
        """Thread that streams video to clients"""
        while self.video_thread_is_running:
            try:
                if self.tcp_server.isVideoServerConnected():
                    print("Video client connected, starting stream...")
                    self.camera.start_stream()
                    while self.tcp_server.isVideoServerConnected():
                        frame = self.camera.get_frame()
                        if frame:
                            lenFrame = len(frame)
                            lengthBin = struct.pack('<I', lenFrame)
                            try:
                                self.tcp_server.sendDataToVideoClient(lengthBin)
                                self.tcp_server.sendDataToVideoClient(frame)
                            except Exception as e:
                                print(f"Error sending video frame: {e}")
                                break
                    self.camera.stop_stream()
                    print("Video client disconnected")
                time.sleep(0.1)
            except Exception as e:
                print(f"Error in video send thread: {e}")
                time.sleep(0.5)

    def threading_connection_monitor(self):
        """Thread that monitors connection status and updates LED"""
        last_status = None
        while hasattr(self, 'connection_monitor_running') and self.connection_monitor_running:
            try:
                # Check if any client is connected (command or video server)
                is_connected = self.tcp_server.isCmdServerConnected() or self.tcp_server.isVideoServerConnected()
                
                # Update shared status
                with self.connection_status.get_lock():
                    self.connection_status.value = 1 if is_connected else 0
                
                # Update LED color if status changed
                if is_connected != last_status:
                    if is_connected:
                        print("Client connected - LED changing to blue")
                        self.queue_led.put("CMD_LED#4#0#0#255#0")  # Blue breathing
                    else:
                        print("Client disconnected - LED changing to red")
                        self.queue_led.put("CMD_LED#4#255#0#0#0")  # Red breathing
                    last_status = is_connected
                
                time.sleep(0.5)  # Check every 500ms
            except Exception as e:
                print(f"Error in connection monitor thread: {e}")
                time.sleep(1)

    def set_process_led_running(self, state):
        """Start or stop LED process"""
        if state and not self.led_process_is_running:
            self.led_process_is_running = True
            self.led_process = multiprocessing.Process(target=self.process_led_running, args=(self.queue_led, self.connection_status), daemon=True)
            self.led_process.start()
            print("LED process started")
        elif not state and self.led_process_is_running:
            self.led_process_is_running = False
            if self.led_process:
                self.led_process.terminate()
                self.led_process.join(0.5)
            print("LED process stopped")

    def process_led_running(self, queue_led, connection_status):
        """Process that handles LED effects - must create own instances in process"""
        # Create LED and parser instances in this process (multiprocessing requirement)
        from led import Led
        from message import MessageParser
        led = Led()
        led_parser = MessageParser()
        # Default to breathing mode with red color (255, 0, 0) - no connection
        # Format: [mode, R, G, B, index]
        # Mode 4 = breathing effect
        led_parameters = [4, 255, 0, 0, 0]
        current_color = [255, 0, 0]  # Track current color [R, G, B]
        
        # Use a flag that can be checked in the process
        # Since we can't directly check self.led_process_is_running from another process,
        # we'll use a timeout-based approach or check queue for shutdown signal
        try:
            while True:  # Will break when process is terminated
                # Check for new LED commands from queue
                if not queue_led.empty():
                    queue_buf_cmd = queue_led.get()
                    led_parser.clearParameters()
                    led_parser.parser(queue_buf_cmd)
                    led_parameters = led_parser.intParameter
                    # Update current color if it's a breathing command
                    if led_parameters[0] == 4 and len(led_parameters) >= 4:
                        current_color = [led_parameters[1], led_parameters[2], led_parameters[3]]
                
                # Check connection status and update color if needed
                with connection_status.get_lock():
                    is_connected = connection_status.value == 1
                
                # Update LED color based on connection status
                if is_connected:
                    # Client connected - use blue
                    if current_color != [0, 0, 255]:
                        current_color = [0, 0, 255]
                        led_parameters = [4, 0, 0, 255, 0]
                else:
                    # No client - use red
                    if current_color != [255, 0, 0]:
                        current_color = [255, 0, 0]
                        led_parameters = [4, 255, 0, 0, 0]
                
                # Execute LED effects
                while queue_led.empty():
                    if led_parameters[0] == 1:
                        led.ledIndex(led_parameters[4], led_parameters[1], led_parameters[2], led_parameters[3])
                        time.sleep(0.1)
                    elif led_parameters[0] == 2:
                        led.colorWipe((255, 0, 0), 120)
                        led.colorWipe((0, 255, 0), 120)
                        led.colorWipe((0, 0, 255), 120)
                        led.colorWipe((0, 0, 0), 120)
                    elif led_parameters[0] == 3:
                        led.Blink(led_parameters[1:4], 50)
                        led.Blink((0, 0, 0), 50)
                    elif led_parameters[0] == 4:
                        led.Breathing(led_parameters[1:4])
                    elif led_parameters[0] == 5:
                        led.rainbowCycle()
                    else:
                        led.colorWipe((0, 0, 0), 10)
                        break
                time.sleep(0.01)
        except KeyboardInterrupt:
            led.colorWipe((0, 0, 0), 10)
        except Exception as e:
            print(f"Error in LED process: {e}")
            led.colorWipe((0, 0, 0), 10)

if __name__ == '__main__':
    server = HeadlessServer()
    try:
        server.start()
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()

