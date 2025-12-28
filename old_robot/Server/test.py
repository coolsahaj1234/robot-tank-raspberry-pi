def test_Parameter():
    from parameter import ParameterManager               # Import the ParameterManager class from the parameter module
    manager = ParameterManager()                         # Initialize the ParameterManager instance
    if manager.file_exists("params.json") and manager.validate_params("params.json"):  # Check if the params.json file exists and is valid
        pcb_version = manager.get_pcb_version()          # Get the PCB version
        print(f"PCB Version: {pcb_version}.0")           # Print the PCB version
        pi_version = manager.get_raspberry_pi_version()  # Get the Raspberry Pi version
        print(f"Raspberry PI version is {'less than 5' if pi_version == 1 else '5'}.")  # Print the Raspberry Pi version

def test_Led():
    from led import Led                        # Import the Led class from the led module
    import time                                # Import the time module for sleep functionality
    print('Program is starting ... ')          # Print a start message
    led = Led()                                # Initialize the Led instance
    try:
        while True:
            print("ledIndex test")             # Print a test message
            led.ledIndex(0x01, 255, 0, 0)      # Set LED 1 to red
            led.ledIndex(0x02, 0, 255, 0)      # Set LED 2 to green
            led.ledIndex(0x04, 0, 0, 255)      # Set LED 3 to blue
            led.ledIndex(0x08, 255, 255, 255)  # Set LED 4 to white
            time.sleep(3)                      # Wait for 3 seconds

            print("colorWipe test")            # Print a test message
            led.colorWipe((255, 0, 0))         # Perform a red color wipe
            led.colorWipe((0, 255, 0))         # Perform a green color wipe
            led.colorWipe((0, 0, 255))         # Perform a blue color wipe
            time.sleep(1)                      # Wait for 1 second

            print("theaterChaseRainbow test")  # Print a test message
            led.theaterChaseRainbow()          # Perform a theater chase rainbow effect
            print("rainbow test")              # Print a test message
            led.rainbow()                      # Perform a rainbow effect
            print("rainbowCycle test")         # Print a test message
            led.rainbowCycle()                 # Perform a rainbow cycle effect

            led.colorWipe((0, 0, 0), 10)       # Turn off all LEDs
    except KeyboardInterrupt:                  # Handle keyboard interrupt (Ctrl+C)
        led.colorWipe((0, 0, 0), 10)           # Turn off all LEDs
        print("\nEnd of program")              # Print an end message

def test_Motor():
    from motor import tankMotor              # Import the tankMotor class from the motor module
    import time                              # Import the time module for sleep functionality
    print('Program is starting ... ')        # Print a start message
    PWM = tankMotor()                        # Initialize the tankMotor instance
    try:
        PWM.setMotorModel(2000, 2000)        # Move the car forward
        print("The car is moving forward")   # Print a status message
        time.sleep(1)                        # Wait for 1 second
        PWM.setMotorModel(-2000, -2000)      # Move the car backward
        print("The car is going backwards")  # Print a status message
        time.sleep(1)                        # Wait for 1 second
        PWM.setMotorModel(-2000, 2000)       # Turn the car left
        print("The car is turning left")     # Print a status message
        time.sleep(1)                        # Wait for 1 second
        PWM.setMotorModel(2000, -2000)       # Turn the car right
        print("The car is turning right")    # Print a status message
        time.sleep(1)                        # Wait for 1 second
        PWM.setMotorModel(0, 0)              # Stop the car
        print("\nEnd of program")            # Print an end message
    except KeyboardInterrupt:                # Handle keyboard interrupt (Ctrl+C)
        PWM.setMotorModel(0, 0)              # Stop the car
        print("\nEnd of program")            # Print an end message

def test_Ultrasonic():
    from ultrasonic import Ultrasonic  # Import the Ultrasonic class from the ultrasonic module
    import time                        # Import the time module for sleep functionality
    import threading                   # Import threading for concurrent sensor reading

    print('Program is starting ... ')  # Print a start message
    print('Testing both ultrasonic sensors simultaneously')

    # Initialize both ultrasonic sensors
    ultrasonic1 = Ultrasonic(sensor_id=1)  # Sensor 1: trigger=27, echo=22
    ultrasonic2 = Ultrasonic(sensor_id=2)  # Sensor 2: trigger=25, echo=18

    # Flag to control the threads
    running = True

    def read_sensor(sensor, sensor_name):
        """Read distance from a sensor continuously"""
        try:
            while running:
                distance = sensor.get_distance()                    # Get the distance to the obstacle
                print(f"{sensor_name} distance: {distance} CM")     # Print the distance with sensor name
                time.sleep(0.3)                                     # Wait for 0.3 seconds
        except Exception as e:
            print(f"{sensor_name} error: {e}")

    try:
        # Create threads for both sensors
        thread1 = threading.Thread(target=read_sensor, args=(ultrasonic1, "Sensor 1 (GPIO27/22)"))
        thread2 = threading.Thread(target=read_sensor, args=(ultrasonic2, "Sensor 2 (GPIO25/18)"))

        # Start both threads
        thread1.start()
        thread2.start()

        # Wait for threads to finish (they run until KeyboardInterrupt)
        thread1.join()
        thread2.join()

    except KeyboardInterrupt:                                       # Handle keyboard interrupt (Ctrl+C)
        running = False                                             # Stop the threads
        time.sleep(0.5)                                             # Give threads time to finish
        ultrasonic1.close()                                         # Close sensor 1
        ultrasonic2.close()                                         # Close sensor 2
        print("\nEnd of program")                                   # Print an end message

def test_Infrared():
    from infrared import Infrared      # Import the Infrared class from the infrared module
    import time                        # Import the time module for sleep functionality
    print('Program is starting ... ')  # Print a start message
    infrared = Infrared()              # Initialize the Infrared instance
    try:
        while True:
            if infrared.read_one_infrared(1) == 0 and infrared.read_one_infrared(2) == 1 and infrared.read_one_infrared(3) == 0:
                print('Middle')        # Print a middle detection message
            elif infrared.read_one_infrared(1) == 1 and infrared.read_one_infrared(2) == 0 and infrared.read_one_infrared(3) == 1:
                print('Middle')        # Print a middle detection message
            elif infrared.read_one_infrared(1) == 0 and infrared.read_one_infrared(2) == 0 and infrared.read_one_infrared(3) == 1:
                print('Right')         # Print a right detection message
            elif infrared.read_one_infrared(1) == 1 and infrared.read_one_infrared(2) == 1 and infrared.read_one_infrared(3) == 0:
                print('Right')         # Print a right detection message
            elif infrared.read_one_infrared(1) == 1 and infrared.read_one_infrared(2) == 0 and infrared.read_one_infrared(3) == 0:
                print('Left')          # Print a left detection message
            elif infrared.read_one_infrared(1) == 0 and infrared.read_one_infrared(2) == 1 and infrared.read_one_infrared(3) == 1:
                print('Left')          # Print a left detection message
            time.sleep(0.1)            # Wait for 0.1 seconds
    except KeyboardInterrupt:          # Handle keyboard interrupt (Ctrl+C)
        print("\nEnd of program")      # Print an end message

def test_Servo():
    from servo import Servo            # Import the Servo class from the servo module
    import time                        # Import the time module for sleep functionality
    print('Program is starting ... ')  # Print a start message
    print('Servo jitter reduction enabled: debouncing and smoothing active')
    servo = Servo()                    # Initialize the Servo instance
    
    print('Testing servos 0 and 1')
    print('Note: Servo updates are throttled to reduce jitter (min 50ms interval, 1° threshold)')
    # Servo 2 (servo motor 3) disabled - not in use
    # if servo.pcb_version == 2:
    #     print('Testing servos 0, 1, and 2 (PCB v2)')
    #     print('Servo 2 will continuously rotate 360°')
    # else:
    #     print('Testing servos 0 and 1')
    
    try:
        # Servo 2 (servo motor 3) disabled - not in use
        # servo2_angle = 0
        # servo2_direction = 1
        while True:
            # Test servo 0: sweep from 90 to 150
            # Use step size of 2 degrees and longer delay for smoother movement
            for i in range(90, 150, 2):
                servo.setServoAngle('0', i)  # Set servo 0 to angle i (debouncing handled internally)
                # Servo 2 (servo motor 3) disabled - not in use
                # # Rotate servo 2 during servo 0 movement (PCB v2 only)
                # if servo.pcb_version == 2:
                #     servo.setServoAngle('2', servo2_angle)
                #     servo2_angle += servo2_direction * 3
                #     if servo2_angle >= 180:
                #         servo2_direction = -1
                #     elif servo2_angle <= 0:
                #         servo2_direction = 1
                time.sleep(0.08)           # Wait for 80ms (allows debouncing to work, reduces jitter)
            
            # Test servo 1: sweep from 140 to 90
            for i in range(140, 90, -2):
                servo.setServoAngle('1', i)  # Set servo 1 to angle i (debouncing handled internally)
                # Servo 2 (servo motor 3) disabled - not in use
                # # Rotate servo 2 during servo 1 movement (PCB v2 only)
                # if servo.pcb_version == 2:
                #     servo.setServoAngle('2', servo2_angle)
                #     servo2_angle += servo2_direction * 3
                #     if servo2_angle >= 180:
                #         servo2_direction = -1
                #     elif servo2_angle <= 0:
                #         servo2_direction = 1
                time.sleep(0.08)           # Wait for 80ms (allows debouncing to work, reduces jitter)
            
            # Test servo 1: sweep from 90 to 140
            for i in range(90, 140, 2):
                servo.setServoAngle('1', i)  # Set servo 1 to angle i (debouncing handled internally)
                # Servo 2 (servo motor 3) disabled - not in use
                # # Rotate servo 2 during servo 1 movement (PCB v2 only)
                # if servo.pcb_version == 2:
                #     servo.setServoAngle('2', servo2_angle)
                #     servo2_angle += servo2_direction * 3
                #     if servo2_angle >= 180:
                #         servo2_direction = -1
                #     elif servo2_angle <= 0:
                #         servo2_direction = 1
                time.sleep(0.08)           # Wait for 80ms (allows debouncing to work, reduces jitter)
            
            # Test servo 0: sweep from 150 to 90
            for i in range(150, 90, -2):
                servo.setServoAngle('0', i)  # Set servo 0 to angle i (debouncing handled internally)
                # Servo 2 (servo motor 3) disabled - not in use
                # # Rotate servo 2 during servo 0 movement (PCB v2 only)
                # if servo.pcb_version == 2:
                #     servo.setServoAngle('2', servo2_angle)
                #     servo2_angle += servo2_direction * 3
                #     if servo2_angle >= 180:
                #         servo2_direction = -1
                #     elif servo2_angle <= 0:
                #         servo2_direction = 1
                time.sleep(0.08)           # Wait for 80ms (allows debouncing to work, reduces jitter)
    except KeyboardInterrupt:              # Handle keyboard interrupt (Ctrl+C)
        # Force update to ensure servos return to safe positions
        servo.setServoAngle('0', 90, force_update=True)         # Set servo 0 to 90 degrees
        servo.setServoAngle('1', 140, force_update=True)        # Set servo 1 to 140 degrees
        # Servo 2 (servo motor 3) disabled - not in use
        # if servo.pcb_version == 2:
        #     servo.setServoAngle('2', 90, force_update=True)     # Set servo 2 to 90 degrees
        print("\nEnd of program")          # Print an end message
<<<<<<< HEAD
=======
        
def test_IMU():
    from mpu6050 import MPU6050
    import time
    print('Starting IMU test...')
    imu = MPU6050()
    imu.calibrate()
    try:
        while True:
            data = imu.get_motion_data()
            print(f"Accel: X={data['accel']['x']:.2f}, Y={data['accel']['y']:.2f}, Z={data['accel']['z']:.2f} g")
            print(f"Gyro:  X={data['gyro']['x']:.2f}, Y={data['gyro']['y']:.2f}, Z={data['gyro']['z']:.2f} °/s")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nEnd of program")
>>>>>>> 40885bf (Initial commit)

def test_Camera():
    import time
    import threading
    import os
    from camera import Camera         # Import the Camera class from the camera module
    
    def test_single_camera(camera_num):
        """Test a single camera in a separate thread"""
        print(f"Starting camera {camera_num}")
        try:
            camera = Camera(camera_num=camera_num)  # Initialize the Camera instance with specific camera number
            camera.start_image()                     # Start the camera
            print(f"Camera {camera_num} started. Will take a photo after 2 seconds.")
            time.sleep(2)   # Give camera time to initialize
            filename = f"image_cam{camera_num}.jpg"
            camera.save_image(filename)  # Capture an image and save it
            
            # Verify image was created
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                print(f"Camera {camera_num} photo saved as '{filename}' ({file_size} bytes)")
            else:
                print(f"Warning: Camera {camera_num} photo file '{filename}' was not created!")
            
            time.sleep(1)
            camera.close()                           # Close the camera
            print(f"Camera {camera_num} test finished")
        except Exception as e:
            print(f"Camera {camera_num} test failed: {e}")
    
    print("Testing cameras (headless mode - no preview window)")
    print("Images will be saved to current directory")
    
    # Test camera 0 first
    print("\n=== Testing Camera 0 ===")
    test_single_camera(0)
    
    # Try camera 1 if available
    print("\n=== Testing Camera 1 ===")
    try:
        test_single_camera(1)
    except Exception as e:
        print(f"Camera 1 not available or failed: {e}")
        print("(This is normal if you only have one camera connected)")
    
    print("\nCamera test finished. Check for image_cam0.jpg and image_cam1.jpg files.")

# Main program logic follows:
if __name__ == '__main__':
    import sys  # Import the sys module for command-line arguments
    if len(sys.argv) < 2:
        print("Parameter error: Please assign the device")       # Print an error message if no device is specified
        exit()                                                   # Exit the program
    if sys.argv[1] == 'Parameter' or sys.argv[1] == 'parameter':
        test_Parameter()                                         # Run the parameter test
    elif sys.argv[1] == 'Led' or sys.argv[1] == 'led':
        test_Led()                                               # Run the LED test
    elif sys.argv[1] == 'Motor' or sys.argv[1] == 'motor':
        test_Motor()                                             # Run the motor test
    elif sys.argv[1] == 'Ultrasonic' or sys.argv[1] == 'ultrasonic':
        test_Ultrasonic()                                        # Run the ultrasonic test
    elif sys.argv[1] == 'Infrared' or sys.argv[1] == 'infrared':
        test_Infrared()                                          # Run the infrared test
    elif sys.argv[1] == 'Servo' or sys.argv[1] == 'servo':
        test_Servo()                                             # Run the servo test
<<<<<<< HEAD
=======
    elif sys.argv[1] == 'IMU' or sys.argv[1] == 'imu':
        test_IMU()                                               # Run the IMU test
>>>>>>> 40885bf (Initial commit)
    elif sys.argv[1] == 'Camera' or sys.argv[1] == 'camera':
        test_Camera()                                            # Run the camera test