try:
    import pigpio
    PIGPIO_AVAILABLE = True
except ImportError:
    PIGPIO_AVAILABLE = False
    pigpio = None

class PigpioServo:
    def __init__(self, pcb_version=1):
        # Initialize the PigpioServo instance
        # PCB v1 uses GPIO 7, 8, 19
        # PCB v2 uses GPIO 12, 13, 19
        if pcb_version == 1:
            self.channel1 = 7  # GPIO pin for channel 1 (PCB v1)
            self.channel2 = 8  # GPIO pin for channel 2 (PCB v1)
        else:  # pcb_version == 2
            self.channel1 = 12  # GPIO pin for channel 1 (PCB v2)
            self.channel2 = 13  # GPIO pin for channel 2 (PCB v2)
        self.channel3 = 19  # GPIO pin for channel 3 (both PCB versions)
        self.pcb_version = pcb_version
        
        if not PIGPIO_AVAILABLE:
            raise ImportError("pigpio library is not available. Install it or use gpiozero instead.")
        
        self.PwmServo = pigpio.pi()  # Initialize the pigpio library
        if not self.PwmServo.connected:
            raise ConnectionError("Failed to connect to pigpio daemon. Make sure pigpiod is running: sudo systemctl start pigpiod")
        
        self.PwmServo.set_mode(self.channel1, pigpio.OUTPUT)  # Set channel 1 as output
        self.PwmServo.set_mode(self.channel2, pigpio.OUTPUT)  # Set channel 2 as output
        self.PwmServo.set_mode(self.channel3, pigpio.OUTPUT)  # Set channel 3 as output
        self.PwmServo.set_PWM_frequency(self.channel1, 50)  # Set PWM frequency for channel 1 to 50 Hz
        self.PwmServo.set_PWM_frequency(self.channel2, 50)  # Set PWM frequency for channel 2 to 50 Hz
        self.PwmServo.set_PWM_frequency(self.channel3, 50)  # Set PWM frequency for channel 3 to 50 Hz
        self.PwmServo.set_PWM_range(self.channel1, 4000)  # Set PWM range for channel 1 to 4000
        self.PwmServo.set_PWM_range(self.channel2, 4000)  # Set PWM range for channel 2 to 4000
        self.PwmServo.set_PWM_range(self.channel3, 4000)  # Set PWM range for channel 3 to 4000

    def setServoPwm(self, channel, angle):
        # Set the PWM duty cycle for the specified channel and angle
        if channel == '0':
            self.PwmServo.set_PWM_dutycycle(self.channel1, 80 + (400 / 180) * angle)  # Calculate and set PWM duty cycle for channel 1
        elif channel == '1':
            self.PwmServo.set_PWM_dutycycle(self.channel2, 80 + (400 / 180) * angle)  # Calculate and set PWM duty cycle for channel 2
        elif channel == '2':
            if self.pcb_version == 2:
                self.PwmServo.set_PWM_dutycycle(self.channel3, 80 + (400 / 180) * angle)  # Calculate and set PWM duty cycle for channel 3

    def setServoStop(self, channel):
        # Stop the PWM for the specified channel
        if channel == '0':
            self.PwmServo.set_PWM_dutycycle(self.channel1, 0)  # Stop PWM for channel 1
        elif channel == '1':
            self.PwmServo.set_PWM_dutycycle(self.channel2, 0)  # Stop PWM for channel 2
        elif channel == '2':
            if self.pcb_version == 2:
                self.PwmServo.set_PWM_dutycycle(self.channel3, 0)  # Stop PWM for channel 3

from gpiozero import AngularServo
class GpiozeroServo:
    def __init__(self, pcb_version=1):
        # Initialize the GpiozeroServo instance
        # PCB v1 uses GPIO 7, 8, 19
        # PCB v2 uses GPIO 12, 13, 19
        if pcb_version == 1:
            self.channel1 = 7  # GPIO pin for channel 1 (PCB v1)
            self.channel2 = 8  # GPIO pin for channel 2 (PCB v1)
        else:  # pcb_version == 2
            self.channel1 = 12  # GPIO pin for channel 1 (PCB v2)
            self.channel2 = 13  # GPIO pin for channel 2 (PCB v2)
        self.channel3 = 19  # GPIO pin for channel 3 (both PCB versions)
        self.pcb_version = pcb_version
        
        self.myCorrection = 0.0  # Correction value for pulse width
        self.maxPW = (2.5 + self.myCorrection) / 1000  # Maximum pulse width
        self.minPW = (0.5 - self.myCorrection) / 1000  # Minimum pulse width
        # Use frame_width=20ms (50Hz) for better stability and reduce jitter
        # frame_width controls the PWM period - 20ms = 50Hz standard servo frequency
        self.servo1 = AngularServo(self.channel1, initial_angle=0, min_angle=0, max_angle=180, 
                                   min_pulse_width=self.minPW, max_pulse_width=self.maxPW,
                                   frame_width=0.02)  # 20ms frame = 50Hz
        self.servo2 = AngularServo(self.channel2, initial_angle=0, min_angle=0, max_angle=180, 
                                   min_pulse_width=self.minPW, max_pulse_width=self.maxPW,
                                   frame_width=0.02)  # 20ms frame = 50Hz
        # Servo 2 (servo motor 3) disabled - not in use
        # if self.pcb_version == 2:
        #     self.servo3 = AngularServo(self.channel3, initial_angle=0, min_angle=0, max_angle=180, 
        #                                min_pulse_width=self.minPW, max_pulse_width=self.maxPW,
        #                                frame_width=0.02)  # 20ms frame = 50Hz

    def setServoPwm(self, channel, angle):
        # Direct angle control - no interpolation, no checks, immediate response
        # Setting angle automatically attaches the servo if detached
        if channel == '0':
            self.servo1.angle = angle  # Direct angle control
        elif channel == '1':
            self.servo2.angle = angle  # Direct angle control
        # elif channel == '2': # Servo 2 disabled
        #     if self.pcb_version == 2:
        #         self.servo3.angle = angle

    def setServoStop(self, channel):
        # Stop the servo by detaching (releases the servo)
        if channel == '0':
            self.servo1.detach()  # Detach servo 1
        elif channel == '1':
            self.servo2.detach()  # Detach servo 2
        # elif channel == '2': # Servo 2 disabled
        #     if self.pcb_version == 2:
        #         self.servo3.detach()  # Detach servo 3

from rpi_hardware_pwm import HardwarePWM
class HardwareServo:
    def __init__(self, pcb_version):
        # Initialize the HardwareServo instance
        self.pcb_version = pcb_version  # PCB version
        self.pwm_gpio12 = None  # PWM object for GPIO 12
        self.pwm_gpio13 = None  # PWM object for GPIO 13
        self.pwm_gpio19 = None  # PWM object for GPIO 19
        if self.pcb_version == 1:
            self.pwm_gpio12 = HardwarePWM(pwm_channel=0, hz=50, chip=0)  # Initialize PWM for GPIO 12 on chip 0
            self.pwm_gpio13 = HardwarePWM(pwm_channel=1, hz=50, chip=0)  # Initialize PWM for GPIO 13 on chip 0
        elif self.pcb_version == 2:
            self.pwm_gpio12 = HardwarePWM(pwm_channel=0, hz=50, chip=0)  # Initialize PWM for GPIO 12 (PWM0)
            self.pwm_gpio13 = HardwarePWM(pwm_channel=1, hz=50, chip=0)  # Initialize PWM for GPIO 13 (PWM1)
            self.pwm_gpio19 = HardwarePWM(pwm_channel=3, hz=50, chip=0)  # Initialize PWM for GPIO 19 (PWM3)
        self.pwm_gpio12.start(0)  # Start PWM for GPIO 12 with 0% duty cycle
        self.pwm_gpio13.start(0)  # Start PWM for GPIO 13 with 0% duty cycle
        if self.pcb_version == 2:
            self.pwm_gpio19.start(0)  # Start PWM for GPIO 19 with 0% duty cycle

    def setServoStop(self, channel):
        # Stop the PWM for the specified channel
        if channel == '0':
            self.pwm_gpio12.stop()  # Stop PWM for GPIO 12
        elif channel == '1':
            self.pwm_gpio13.stop()  # Stop PWM for GPIO 13
        elif channel == '2':
            if self.pcb_version == 2:
                self.pwm_gpio19.stop()  # Stop PWM for GPIO 19

    def setServoFrequency(self, channel, freq):
        # Set the PWM frequency for the specified channel
        if channel == '0':
            self.pwm_gpio12.change_frequency(freq)  # Change frequency for GPIO 12
        elif channel == '1':
            self.pwm_gpio13.change_frequency(freq)  # Change frequency for GPIO 13
        elif channel == '2':
            if self.pcb_version == 2:
                self.pwm_gpio19.change_frequency(freq)  # Change frequency for GPIO 19

    def setServoDuty(self, channel, duty):
        # Set the PWM duty cycle for the specified channel
        if channel == '0':
            self.pwm_gpio12.change_duty_cycle(duty)  # Change duty cycle for GPIO 12
        elif channel == '1':
            self.pwm_gpio13.change_duty_cycle(duty)  # Change duty cycle for GPIO 13
        elif channel == '2':
            if self.pcb_version == 2:
                self.pwm_gpio19.change_duty_cycle(duty)  # Change duty cycle for GPIO 19

    def map(self, x, in_min, in_max, out_min, out_max):
        # Map a value from one range to another
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def setServoPwm(self, channel, angle):
        # Set the PWM duty cycle for the specified channel and angle
        if channel == '0':
            duty = self.map(angle, 0, 180, 2.5, 12.5)  # Map angle to duty cycle
            self.setServoDuty(channel, duty)  # Set duty cycle for GPIO 12
        elif channel == '1':
            duty = self.map(angle, 0, 180, 2.5, 12.5)  # Map angle to duty cycle
            self.setServoDuty(channel, duty)  # Set duty cycle for GPIO 13
        elif channel == '2':
            if self.pcb_version == 2:
                duty = self.map(angle, 0, 180, 2.5, 12.5)  # Map angle to duty cycle
                self.setServoDuty(channel, duty)  # Set duty cycle for GPIO 19

from parameter import ParameterManager
import time
import threading

class Servo:
    def __init__(self):
        # Initialize the Servo instance
        self.param = ParameterManager()  # Initialize parameter manager
        self.pcb_version = self.param.get_pcb_version()  # Get PCB version
        self.pi_version = self.param.get_raspberry_pi_version()  # Get Raspberry Pi version

        if self.pcb_version == 1 and self.pi_version == 1:
            if PIGPIO_AVAILABLE:
                self.pwm = PigpioServo(1)  # Use PigpioServo for PCB version 1 and Raspberry Pi version 1
            else:
                print("Warning: pigpio not available, using gpiozero instead")
                self.pwm = GpiozeroServo(1)  # Fallback to gpiozero
        elif self.pcb_version == 1 and self.pi_version == 2:
            self.pwm = GpiozeroServo(1)  # Use GpiozeroServo for PCB version 1 and Raspberry Pi version 2
        elif self.pcb_version == 2 and self.pi_version == 1:
            # Pi 0 2W and other non-Pi5 boards: try pigpio first, fallback to gpiozero
            if PIGPIO_AVAILABLE:
                try:
                    self.pwm = PigpioServo(2)  # Use PigpioServo for PCB version 2 and Raspberry Pi version 1 (Pi 0 2W, etc.)
                except Exception as e:
                    print(f"Warning: pigpio initialization failed ({e}), using gpiozero instead")
                    self.pwm = GpiozeroServo(2)  # Fallback to gpiozero
            else:
                print("Info: pigpio not available, using gpiozero for servo control")
                self.pwm = GpiozeroServo(2)  # Use gpiozero for PCB version 2 and Raspberry Pi version 1
        elif self.pcb_version == 2 and self.pi_version == 2:
            self.pwm = HardwareServo(2)  # Use HardwareServo for PCB version 2 and Raspberry Pi version 2 (Pi 5 only)
        
        # Servo idle management - detach when not in use to prevent jitter
        self.servo_lock = threading.Lock()  # Lock for thread-safe servo updates
        self.servo_active = {'0': False, '1': False}  # Track if servos are actively moving
        self.servo_idle_timeout = 2.0  # Detach servo after 2 seconds of no movement (longer to avoid interference)
        self.servo_last_activity = {'0': 0, '1': 0}  # Track last activity time
        self.servo_thread_running = True  # Flag to control idle timeout thread
        
        # Set initial positions then immediately detach to prevent jitter at startup
        self.pwm.setServoPwm("0", 90)  # Set initial angle for servo 0
        self.pwm.setServoPwm("1", 140)  # Set initial angle for servo 1
        time.sleep(0.1)  # Brief delay to let servos reach initial position
        
        # Detach servos immediately after initialization to prevent jitter
        self._detach_servo('0')
        self._detach_servo('1')
        print("Servos initialized and detached - will activate on command")
        
        # Start idle timeout thread (only for detaching, no interpolation)
        self.servo_thread = threading.Thread(target=self._servo_idle_thread, daemon=True)
        self.servo_thread.start()

    def angle_range(self, channel, init_angle):
        # Ensure the angle is within the valid range for the specified channel
        if channel == '0':
            if init_angle < 90:
                init_angle = 90  # Minimum angle for channel 0
            elif init_angle > 150:
                init_angle = 150  # Maximum angle for channel 0
        elif channel == '1':
            if init_angle < 90:
                init_angle = 90  # Minimum angle for channel 1
            elif init_angle > 150:
                init_angle = 150  # Maximum angle for channel 1
        elif channel == '2':
            if init_angle < 0:
                init_angle = 0  # Minimum angle for channel 2
            elif init_angle > 180:
                init_angle = 180  # Maximum angle for channel 2
        return init_angle

    def _attach_servo(self, channel):
        """Attach/activate a servo - setting angle will automatically activate for gpiozero"""
        # For gpiozero, setting angle automatically activates the servo
        # For pigpio/hardware PWM, PWM is always active, no action needed
        pass
    
    def _detach_servo(self, channel):
        """Detach/deactivate a servo to prevent jitter when idle"""
        try:
            if hasattr(self.pwm, 'setServoStop'):
                # For HardwareServo and PigpioServo
                self.pwm.setServoStop(channel)
            elif hasattr(self.pwm, 'servo1') and isinstance(self.pwm, GpiozeroServo):
                # For GpiozeroServo - detach stops PWM output
                if channel == '0':
                    self.pwm.servo1.detach()
                elif channel == '1':
                    self.pwm.servo2.detach()
        except Exception as e:
            # Silently fail - some servo types may not support detach
            pass
    
    def _servo_idle_thread(self):
        """Background thread that detaches servos after idle timeout (no interpolation - direct control only)"""
        while self.servo_thread_running:
            try:
                current_time = time.time()
                with self.servo_lock:
                    # Check for idle timeout and detach servos
                    for channel in ['0', '1']:
                        if self.servo_active[channel]:
                            time_since_activity = current_time - self.servo_last_activity[channel]
                            if time_since_activity >= self.servo_idle_timeout:
                                # Detach servo after idle timeout to prevent jitter
                                self._detach_servo(channel)
                                self.servo_active[channel] = False
                
                time.sleep(0.1)  # Check every 100ms
            except Exception as e:
                print(f"Error in servo idle thread: {e}")
                time.sleep(0.1)

    def setServoAngle(self, channel, angle, force_update=False):
        # Direct servo control - no interpolation, no smoothing, immediate response
        channel_str = str(channel)
        angle = self.angle_range(channel_str, int(angle))  # Ensure the angle is within the valid range
        angle_int = int(angle)
        
        with self.servo_lock:
            # Reactivate servo if it was detached
            if not self.servo_active.get(channel_str, False):
                self.servo_active[channel_str] = True
            
            # Direct control - set angle immediately, no interpolation
            self.pwm.setServoPwm(channel_str, angle_int)
            self.servo_last_activity[channel_str] = time.time()  # Reset idle timer

    def setServoStop(self):
        # Stop the PWM for all servos and stop interpolation thread
        self.servo_thread_running = False
        if self.servo_thread:
            self.servo_thread.join(0.5)
        
        if hasattr(self.pwm, 'setServoStop'):
            if self.pcb_version == 2:
                self.pwm.setServoStop('0')  # Stop PWM for servo 0
                self.pwm.setServoStop('1')  # Stop PWM for servo 1
                # Servo 2 (servo motor 3) disabled - not in use
                # self.pwm.setServoStop('2')  # Stop PWM for servo 2
            else:
                self.pwm.setServoStop('0')  # Stop PWM for servo 0
                self.pwm.setServoStop('1')  # Stop PWM for servo 1

# Main program logic follows:
if __name__ == '__main__':
    import time
    servo = Servo()  # Create an instance of the Servo class

    print("Now servo 0 will be rotated to 150°, servo 1 will be rotated to 90°.")
    # Servo 2 (servo motor 3) disabled - not in use
    # if servo.pcb_version == 2:
    #     print("Servo 2 will continuously rotate 360° (0-180-0 sweep for continuous rotation servo).")
    print("If they were already at those angles, nothing would be observed.")
    print("Please keep the program running when installing the servos.")
    print("After that, you can press ctrl-C to end the program.")

    try:
        # Servo 2 (servo motor 3) disabled - not in use
        # servo2_angle = 0
        # servo2_direction = 1
        while True:
            servo.setServoAngle('0', 150)  # Set the angle for servo 0 to 150°
            servo.setServoAngle('1', 90)   # Set the angle for servo 1 to 90°
            # Servo 2 (servo motor 3) disabled - not in use
            # if servo.pcb_version == 2:
            #     # Continuously rotate servo 2 through full range (0-180-0)
            #     servo.setServoAngle('2', servo2_angle)
            #     servo2_angle += servo2_direction * 2  # Increment by 2 degrees
            #     if servo2_angle >= 180:
            #         servo2_direction = -1  # Reverse direction
            #     elif servo2_angle <= 0:
            #         servo2_direction = 1   # Reverse direction
            time.sleep(0.02)  # Small delay for smooth rotation
    except KeyboardInterrupt:
        # Gradually decrease the angle of servo 0 from 150° to 90°
        for i in range(150, 90, -1):
            servo.setServoAngle('0', i)
            time.sleep(0.01)  # Wait for 0.01 seconds between each step

        # Gradually increase the angle of servo 1 from 90° to 140°
        for i in range(90, 140, 1):
            servo.setServoAngle('1', i)
            time.sleep(0.01)  # Wait for 0.01 seconds between each step

        # Servo 2 (servo motor 3) disabled - not in use
        # # Gradually decrease the angle of servo 2 from 180° to 90° (PCB v2 only)
        # if servo.pcb_version == 2:
        #     for i in range(180, 90, -1):
        #         servo.setServoAngle('2', i)
        #         time.sleep(0.01)  # Wait for 0.01 seconds between each step

        servo.setServoStop()  # Stop the servos
        print("\nEnd of program")  # Print a message indicating the end of the program
