import smbus
import time

class MPU6050:
    # MPU6050 Default I2C address
    DEVICE_ADDRESS = 0x68

    # MPU6050 Register map
    PWR_MGMT_1   = 0x6B
    SMPLRT_DIV   = 0x19
    CONFIG       = 0x1A
    GYRO_CONFIG  = 0x1B
    INT_ENABLE   = 0x38
    ACCEL_XOUT_H = 0x3B
    ACCEL_XOUT_L = 0x3C
    ACCEL_YOUT_H = 0x3D
    ACCEL_YOUT_L = 0x3E
    ACCEL_ZOUT_H = 0x3F
    ACCEL_ZOUT_L = 0x40
    GYRO_XOUT_H  = 0x43
    GYRO_XOUT_L  = 0x44
    GYRO_YOUT_H  = 0x45
    GYRO_YOUT_L  = 0x46
    GYRO_ZOUT_H  = 0x47
    GYRO_ZOUT_L  = 0x48

    def __init__(self, bus=1):
        self.bus = smbus.SMBus(bus)
        self.init_mpu()
        
        # Calibration offsets
        self.ax_offset = 0
        self.ay_offset = 0
        self.az_offset = 0
        self.gx_offset = 0
        self.gy_offset = 0
        self.gz_offset = 0

    def init_mpu(self):
        # Write to sample rate register
        self.bus.write_byte_data(self.DEVICE_ADDRESS, self.SMPLRT_DIV, 7)
        # Write to power management register
        self.bus.write_byte_data(self.DEVICE_ADDRESS, self.PWR_MGMT_1, 1)
        # Write to Configuration register
        self.bus.write_byte_data(self.DEVICE_ADDRESS, self.CONFIG, 0)
        # Write to Gyro configuration register
        self.bus.write_byte_data(self.DEVICE_ADDRESS, self.GYRO_CONFIG, 24)
        # Write to interrupt enable register
        self.bus.write_byte_data(self.DEVICE_ADDRESS, self.INT_ENABLE, 1)

    def read_raw_data(self, addr):
        # Accelero and Gyro value are 16-bit
        high = self.bus.read_byte_data(self.DEVICE_ADDRESS, addr)
        low = self.bus.read_byte_data(self.DEVICE_ADDRESS, addr+1)
        # Concatenate higher and lower value
        value = ((high << 8) | low)
        # To get signed value from mpu6050
        if(value > 32768):
            value = value - 65536
        return value

    def get_motion_data(self):
        # Read Accelerometer raw value
        acc_x = self.read_raw_data(self.ACCEL_XOUT_H)
        acc_y = self.read_raw_data(self.ACCEL_YOUT_H)
        acc_z = self.read_raw_data(self.ACCEL_ZOUT_H)

        # Read Gyroscope raw value
        gyro_x = self.read_raw_data(self.GYRO_XOUT_H)
        gyro_y = self.read_raw_data(self.GYRO_YOUT_H)
        gyro_z = self.read_raw_data(self.GYRO_ZOUT_H)

        # Full scale range +/- 2g (default) for accel
        # Sensitivity scale factor 16384 LSB/g
        Ax = acc_x / 16384.0
        Ay = acc_y / 16384.0
        Az = acc_z / 16384.0

        # Full scale range +/- 250 deg/s (default) for gyro
        # Sensitivity scale factor 131 LSB/deg/s
        Gx = gyro_x / 131.0
        Gy = gyro_y / 131.0
        Gz = gyro_z / 131.0

        return {
            'accel': {'x': Ax - self.ax_offset, 'y': Ay - self.ay_offset, 'z': Az - self.az_offset},
            'gyro': {'x': Gx - self.gx_offset, 'y': Gy - self.gy_offset, 'z': Gz - self.gz_offset}
        }

    def calibrate(self, samples=100):
        print(f"Calibrating MPU6050 with {samples} samples... Keep it still!")
        ax, ay, az, gx, gy, gz = 0, 0, 0, 0, 0, 0
        for _ in range(samples):
            data = self.get_motion_data()
            ax += data['accel']['x']
            ay += data['accel']['y']
            az += data['accel']['z']
            gx += data['gyro']['x']
            gy += data['gyro']['y']
            gz += data['gyro']['z']
            time.sleep(0.01)
        
        self.ax_offset = ax / samples
        self.ay_offset = ay / samples
        self.az_offset = (az / samples) - 1.0 # Gravity should be 1.0g on Z if flat
        self.gx_offset = gx / samples
        self.gy_offset = gy / samples
        self.gz_offset = gz / samples
        print("Calibration complete.")
        print(f"Offsets: Accel({self.ax_offset:.2f}, {self.ay_offset:.2f}, {self.az_offset:.2f}), Gyro({self.gx_offset:.2f}, {self.gy_offset:.2f}, {self.gz_offset:.2f})")

if __name__ == '__main__':
    mpu = MPU6050()
    mpu.calibrate()
    try:
        while True:
            data = mpu.get_motion_data()
            print(f"Accel: X={data['accel']['x']:.2f}, Y={data['accel']['y']:.2f}, Z={data['accel']['z']:.2f} g")
            print(f"Gyro: X={data['gyro']['x']:.2f}, Y={data['gyro']['y']:.2f}, Z={data['gyro']['z']:.2f} °/s")
            print("-" * 20)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Test stopped")
