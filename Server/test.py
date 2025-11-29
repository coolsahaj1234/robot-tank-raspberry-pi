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
    servo = Servo()                    # Initialize the Servo instance
    
    if servo.pcb_version == 2:
        print('Testing servos 0, 1, and 2 (PCB v2)')
        print('Servo 2 will continuously rotate 360°')
    else:
        print('Testing servos 0 and 1')
    
    try:
        servo2_angle = 0
        servo2_direction = 1
        while True:
            # Test servo 0: sweep from 90 to 150
            for i in range(90, 150, 1):
                servo.setServoAngle('0', i)  # Set servo 0 to angle i
                # Rotate servo 2 during servo 0 movement (PCB v2 only)
                if servo.pcb_version == 2:
                    servo.setServoAngle('2', servo2_angle)
                    servo2_angle += servo2_direction * 3
                    if servo2_angle >= 180:
                        servo2_direction = -1
                    elif servo2_angle <= 0:
                        servo2_direction = 1
                time.sleep(0.01)           # Wait for 0.01 seconds
            
            # Test servo 1: sweep from 140 to 90
            for i in range(140, 90, -1):
                servo.setServoAngle('1', i)  # Set servo 1 to angle i
                # Rotate servo 2 during servo 1 movement (PCB v2 only)
                if servo.pcb_version == 2:
                    servo.setServoAngle('2', servo2_angle)
                    servo2_angle += servo2_direction * 3
                    if servo2_angle >= 180:
                        servo2_direction = -1
                    elif servo2_angle <= 0:
                        servo2_direction = 1
                time.sleep(0.01)           # Wait for 0.01 seconds
            
            # Test servo 1: sweep from 90 to 140
            for i in range(90, 140, 1):
                servo.setServoAngle('1', i)  # Set servo 1 to angle i
                # Rotate servo 2 during servo 1 movement (PCB v2 only)
                if servo.pcb_version == 2:
                    servo.setServoAngle('2', servo2_angle)
                    servo2_angle += servo2_direction * 3
                    if servo2_angle >= 180:
                        servo2_direction = -1
                    elif servo2_angle <= 0:
                        servo2_direction = 1
                time.sleep(0.01)           # Wait for 0.01 seconds
            
            # Test servo 0: sweep from 150 to 90
            for i in range(150, 90, -1):
                servo.setServoAngle('0', i)  # Set servo 0 to angle i
                # Rotate servo 2 during servo 0 movement (PCB v2 only)
                if servo.pcb_version == 2:
                    servo.setServoAngle('2', servo2_angle)
                    servo2_angle += servo2_direction * 3
                    if servo2_angle >= 180:
                        servo2_direction = -1
                    elif servo2_angle <= 0:
                        servo2_direction = 1
                time.sleep(0.01)           # Wait for 0.01 seconds
    except KeyboardInterrupt:              # Handle keyboard interrupt (Ctrl+C)
        servo.setServoAngle('0', 90)         # Set servo 0 to 90 degrees
        servo.setServoAngle('1', 140)        # Set servo 1 to 140 degrees
        if servo.pcb_version == 2:
            servo.setServoAngle('2', 90)     # Set servo 2 to 90 degrees
        print("\\nEnd of program")          # Print an end message

def test_Camera():
    import time
    import threading
    from camera import Camera         # Import the Camera class from the camera module
    
    def test_single_camera(camera_num):
        """Test a single camera in a separate thread"""
        print(f"Starting camera {camera_num}")
        camera = Camera(camera_num=camera_num)  # Initialize the Camera instance with specific camera number
        camera.start_image()                     # Start the camera
        print(f"Camera {camera_num} preview started. Will take a photo after 5 seconds.")
        time.sleep(5)   
        camera.save_image(f"image_cam{camera_num}.jpg")  # Capture an image and save it
        print(f"Camera {camera_num} photo saved as 'image_cam{camera_num}.jpg'")
        time.sleep(2)  # Keep the preview open for a bit longer
        camera.close()                           # Close the camera
        print(f"Camera {camera_num} test finished")
    
    print("Testing both cameras simultaneously")
    
    # Create threads for both cameras
    thread0 = threading.Thread(target=test_single_camera, args=(0,))
    thread1 = threading.Thread(target=test_single_camera, args=(1,))
    
    # Start both threads
    thread0.start()
    thread1.start()
    
    # Wait for both threads to complete
    thread0.join()
    thread1.join()
    
    print("Both camera tests finished")

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
    elif sys.argv[1] == 'Camera' or sys.argv[1] == 'camera':
        test_Camera()                                            # Run the camera test