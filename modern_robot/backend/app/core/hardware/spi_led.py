import spidev
import numpy as np
import time

class Freenove_SPI_LedPixel(object):
    def __init__(self, count=8, bright=255, sequence='GRB', bus=0, device=0):
        self.set_led_type(sequence)
        self.set_led_count(count)
        self.set_led_brightness(bright)
        self.led_begin(bus, device)
        self.set_all_led_color(0, 0, 0)
       
    def led_begin(self, bus=0, device=0):
        self.bus = bus
        self.device = device
        try:
            self.spi = spidev.SpiDev()
            self.spi.open(self.bus, self.device)
            self.spi.mode = 0
            self.led_init_state = 1
        except OSError:
            print("SPI Init Failed. Ensure SPI is enabled (sudo raspi-config > Interface Options > SPI).")
            self.led_init_state = 0
            
    def led_close(self):
        self.set_all_led_rgb([0, 0, 0])
        self.spi.close()
    
    def set_led_count(self, count):
        self.led_count = count
        self.led_color = [0, 0, 0] * self.led_count
        self.led_original_color = [0, 0, 0] * self.led_count
    
    def get_led_count(self):
        return self.led_count
        
    def set_led_type(self, rgb_type):
        try:
            led_type = ['RGB', 'RBG', 'GRB', 'GBR', 'BRG', 'BGR']
            led_type_offset = [0x06, 0x09, 0x12, 0x21, 0x18, 0x24]
            index = led_type.index(rgb_type)
            self.led_red_offset = (led_type_offset[index] >> 4) & 0x03
            self.led_green_offset = (led_type_offset[index] >> 2) & 0x03
            self.led_blue_offset = (led_type_offset[index] >> 0) & 0x03
            return index
        except ValueError:
            self.led_red_offset = 1
            self.led_green_offset = 0
            self.led_blue_offset = 2
            return -1
    
    def set_led_brightness(self, brightness):
        self.led_brightness = brightness
        for i in range(self.get_led_count()):
            self.set_led_rgb_data(i, self.led_original_color)
            
    def set_ledpixel(self, index, r, g, b):
        p = [0, 0, 0]
        p[self.led_red_offset] = round(r * self.led_brightness / 255)
        p[self.led_green_offset] = round(g * self.led_brightness / 255)
        p[self.led_blue_offset] = round(b * self.led_brightness / 255)
        self.led_original_color[index * 3 + self.led_red_offset] = r
        self.led_original_color[index * 3 + self.led_green_offset] = g
        self.led_original_color[index * 3 + self.led_blue_offset] = b
        for i in range(3):
            self.led_color[index * 3 + i] = p[i]

    def set_led_rgb_data(self, index, color):
        self.set_ledpixel(index, color[0], color[1], color[2])   
        
    def set_all_led_rgb_data(self, color):
        for i in range(self.get_led_count()):
            self.set_led_rgb_data(i, color)   
        
    def set_all_led_color(self, r, g, b):
        for i in range(self.get_led_count()):
            self.set_ledpixel(i, r, g, b)
        self.show()
        
    def set_PixelColor(self, index, color):
        # Compatibility wrapper for Adafruit_NeoPixel interface
        # Color is expected to be an integer 0xRRGGBB or tuple
        if isinstance(color, int):
            r = (color >> 16) & 0xFF
            g = (color >> 8) & 0xFF
            b = color & 0xFF
            self.set_ledpixel(index, r, g, b)
        else:
            # Assuming object with red, green, blue attr or tuple
            # If it's a tuple/list
            try:
                self.set_ledpixel(index, color[0], color[1], color[2])
            except:
                pass

    def numPixels(self):
        return self.led_count

    def write_ws2812_numpy8(self):
        d = np.array(self.led_color).ravel()
        tx = np.zeros(len(d) * 8, dtype=np.uint8)
        for ibit in range(8):
            tx[7 - ibit::8] = ((d >> ibit) & 1) * 0x78 + 0x80
        if self.led_init_state != 0:
            if self.bus == 0:
                self.spi.xfer(tx.tolist(), int(8 / 1.25e-6))
            else:
                self.spi.xfer(tx.tolist(), int(8 / 1.0e-6))
        
    def show(self):
        self.write_ws2812_numpy8()





