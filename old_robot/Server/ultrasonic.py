from gpiozero import DistanceSensor, PWMSoftwareFallback
import warnings

class Ultrasonic:
    def __init__(self, sensor_id=1):
        # Initialize the Ultrasonic class and set up the distance sensor.
        # sensor_id: 1 for first sensor (default), 2 for second sensor
        warnings.filterwarnings("ignore", category=PWMSoftwareFallback)  # Ignore PWM software fallback warnings

        if sensor_id == 1:
            self.trigger_pin = 27  # First sensor trigger pin
            self.echo_pin = 22     # First sensor echo pin
        elif sensor_id == 2:
            self.trigger_pin = 25  # Second sensor trigger pin
            self.echo_pin = 18     # Second sensor echo pin
        else:
            raise ValueError(f"Invalid sensor_id: {sensor_id}. Must be 1 or 2.")

        self.sensor_id = sensor_id
        self.sensor = DistanceSensor(echo=self.echo_pin, trigger=self.trigger_pin, max_distance=3)  # Initialize the distance sensor

    def get_distance(self):
        # Get the distance measurement from the ultrasonic sensor in centimeters.
        distance_cm = self.sensor.distance * 100  # Convert distance from meters to centimeters
        return round(float(distance_cm), 1)       # Return the distance rounded to one decimal place

    def close(self):
        # Close the distance sensor.
        self.sensor.close()        # Close the sensor to release resources

if __name__ == '__main__':
    import time      # Import the time module for sleep functionality
    import sys       # Import the sys module for command-line arguments
    import threading # Import threading for concurrent sensor reading

    # Check if sensor_id argument is provided
    if len(sys.argv) > 1:
        sensor_id = int(sys.argv[1])
        ultrasonic = Ultrasonic(sensor_id=sensor_id)  # Initialize the specified sensor
        try:
            while True:
                print("Sensor {} distance: {}cm".format(sensor_id, ultrasonic.get_distance()))  # Print the distance measurement
                time.sleep(0.5)        # Wait for 0.5 seconds
        except KeyboardInterrupt:      # Handle keyboard interrupt (Ctrl+C)
            ultrasonic.close()         # Close the sensor
            print("\nEnd of program")  # Print an end message
    else:
        # Test both sensors simultaneously
        print("Testing both ultrasonic sensors")
        ultrasonic1 = Ultrasonic(sensor_id=1)  # Initialize sensor 1
        ultrasonic2 = Ultrasonic(sensor_id=2)  # Initialize sensor 2

        running = True

        def read_sensor(sensor, sensor_name):
            """Read distance from a sensor continuously"""
            try:
                while running:
                    distance = sensor.get_distance()
                    print(f"{sensor_name} distance: {distance} cm")
                    time.sleep(0.5)
            except Exception as e:
                print(f"{sensor_name} error: {e}")

        try:
            # Create threads for both sensors
            thread1 = threading.Thread(target=read_sensor, args=(ultrasonic1, "Sensor 1 (GPIO27/22)"))
            thread2 = threading.Thread(target=read_sensor, args=(ultrasonic2, "Sensor 2 (GPIO25/18)"))

            # Start both threads
            thread1.start()
            thread2.start()

            # Wait for threads to finish
            thread1.join()
            thread2.join()

        except KeyboardInterrupt:      # Handle keyboard interrupt (Ctrl+C)
            running = False
            time.sleep(0.5)
            ultrasonic1.close()        # Close sensor 1
            ultrasonic2.close()        # Close sensor 2
            print("\nEnd of program")  # Print an end message