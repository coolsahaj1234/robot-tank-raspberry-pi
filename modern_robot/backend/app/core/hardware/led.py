import asyncio
import time
import random
from app.core.config import settings
try:
    from rpi_ws281x import Adafruit_NeoPixel, Color
except ImportError:
    Adafruit_NeoPixel = None
    Color = None

# Import SPI LED fallback
from app.core.hardware.spi_led import Freenove_SPI_LedPixel

class LedController:
    def __init__(self):
        self.is_running = False
        self.mode = "off"
        self.color = (0, 0, 0)
        self.brightness = 255
        self.strip = None
        self.task = None
        self.use_spi = False
        
        if settings.MOCK_MODE:
            print("LedController started in MOCK mode")
            return

        # LED Strip Config
        LED_COUNT = 8      
        LED_PIN = 18       
        LED_FREQ_HZ = 800000 
        LED_DMA = 10       
        LED_INVERT = False 
        LED_CHANNEL = 0    

        # Try initializing standard rpi_ws281x
        if Adafruit_NeoPixel:
            try:
                self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, self.brightness, LED_CHANNEL)
                self.strip.begin()
                print("LED Strip initialized (rpi_ws281x)")
            except Exception as e:
                print(f"Failed to initialize rpi_ws281x: {e}")
                self.strip = None

        # Fallback to SPI if standard failed
        if self.strip is None:
            try:
                self.strip = Freenove_SPI_LedPixel(count=LED_COUNT, bright=self.brightness, sequence='GRB')
                if self.strip.led_init_state == 1:
                    print("LED Strip initialized (SPI)")
                    self.use_spi = True
                else:
                    print("SPI LED initialization reported failure.")
                    self.strip = None
            except Exception as e:
                print(f"Failed to initialize SPI LED: {e}")
                self.strip = None

    async def start(self):
        self.is_running = True
        self.task = asyncio.create_task(self._animation_loop())

    async def stop(self):
        self.is_running = False
        if self.task:
            self.task.cancel()
        self._set_color((0, 0, 0))
        if self.strip and hasattr(self.strip, 'led_close'):
            self.strip.led_close()

    def set_mode(self, mode: str, color: tuple = None):
        self.mode = mode
        if color:
            self.color = color
        print(f"LED Mode set to: {mode} with color {color}")

    def _set_color(self, color):
        if not self.strip: return
        try:
            if self.use_spi:
                self.strip.set_all_led_rgb_data(color)
                self.strip.show()
            else:
                for i in range(self.strip.numPixels()):
                    self.strip.setPixelColor(i, Color(color[0], color[1], color[2]))
                self.strip.show()
        except Exception as e:
            print(f"LED Error: {e}")

    def _set_pixels(self, colors):
        """Set individual pixels. colors is list of (r,g,b) tuples"""
        if not self.strip: return
        try:
            count = self.strip.get_led_count() if self.use_spi else self.strip.numPixels()
            for i in range(min(len(colors), count)):
                c = colors[i]
                if self.use_spi:
                    self.strip.set_led_rgb_data(i, c)
                else:
                    self.strip.setPixelColor(i, Color(c[0], c[1], c[2]))
            self.strip.show()
        except Exception as e:
            print(f"LED Pixel Error: {e}")

    def _get_pixel_count(self):
        if not self.strip: return 0
        return self.strip.get_led_count() if self.use_spi else self.strip.numPixels()

    async def _animation_loop(self):
        while self.is_running:
            if not self.strip:
                await asyncio.sleep(1)
                continue

            try:
                num_pixels = self._get_pixel_count()

                if self.mode == "off":
                    self._set_color((0, 0, 0))
                    await asyncio.sleep(0.5)
                
                elif self.mode == "static":
                    self._set_color(self.color)
                    await asyncio.sleep(0.5)

                elif self.mode == "blink":
                    self._set_color(self.color)
                    await asyncio.sleep(0.5)
                    self._set_color((0, 0, 0))
                    await asyncio.sleep(0.5)

                elif self.mode == "police":
                    half = num_pixels // 2
                    red = (255, 0, 0)
                    blue = (0, 0, 255)
                    colors = [red] * half + [blue] * (num_pixels - half)
                    self._set_pixels(colors)
                    await asyncio.sleep(0.15)
                    colors = [blue] * half + [red] * (num_pixels - half)
                    self._set_pixels(colors)
                    await asyncio.sleep(0.15)

                elif self.mode == "ambulance":
                    half = num_pixels // 2
                    red = (255, 0, 0)
                    white = (255, 255, 255)
                    colors = [red] * half + [white] * (num_pixels - half)
                    self._set_pixels(colors)
                    await asyncio.sleep(0.2)
                    colors = [white] * half + [red] * (num_pixels - half)
                    self._set_pixels(colors)
                    await asyncio.sleep(0.2)

                elif self.mode == "chaser":
                    for i in range(num_pixels):
                        if self.mode != "chaser": break
                        colors = [(0,0,0)] * num_pixels
                        colors[i] = self.color
                        self._set_pixels(colors)
                        await asyncio.sleep(0.1)
                    for i in range(num_pixels - 2, 0, -1):
                        if self.mode != "chaser": break
                        colors = [(0,0,0)] * num_pixels
                        colors[i] = self.color
                        self._set_pixels(colors)
                        await asyncio.sleep(0.1)

                elif self.mode == "fire":
                    colors = []
                    for _ in range(num_pixels):
                        r = random.randint(150, 255)
                        g = random.randint(0, 100)
                        b = 0
                        colors.append((r, g, b))
                    self._set_pixels(colors)
                    await asyncio.sleep(0.05 + random.random() * 0.1)

                elif self.mode == "breath":
                    for i in range(0, 256, 10):
                        if self.mode != "breath": break
                        factor = i / 255.0
                        c = (int(self.color[0] * factor), int(self.color[1] * factor), int(self.color[2] * factor))
                        self._set_color(c)
                        await asyncio.sleep(0.02)
                    for i in range(255, -1, -10):
                        if self.mode != "breath": break
                        factor = i / 255.0
                        c = (int(self.color[0] * factor), int(self.color[1] * factor), int(self.color[2] * factor))
                        self._set_color(c)
                        await asyncio.sleep(0.02)

                elif self.mode == "rainbow":
                    for j in range(256):
                        if self.mode != "rainbow": break
                        if self.use_spi:
                            for i in range(num_pixels):
                                self.strip.set_led_rgb_data(i, self._wheel_tuple((i + j) & 255))
                            self.strip.show()
                        else:
                            for i in range(num_pixels):
                                self.strip.setPixelColor(i, self._wheel((i + j) & 255))
                            self.strip.show()
                        await asyncio.sleep(0.02)

                # ---------------- NEW EFFECTS ----------------

                elif self.mode == "color_wipe":
                    for i in range(num_pixels):
                        if self.mode != "color_wipe": break
                        if self.use_spi:
                            self.strip.set_led_rgb_data(i, self.color)
                            self.strip.show()
                        else:
                            self.strip.setPixelColor(i, Color(self.color[0], self.color[1], self.color[2]))
                            self.strip.show()
                        await asyncio.sleep(0.1)
                    await asyncio.sleep(0.5)
                    self._set_color((0,0,0))

                elif self.mode == "theater_chase":
                    for q in range(3):
                        if self.mode != "theater_chase": break
                        for i in range(0, num_pixels, 3):
                            if i+q < num_pixels:
                                if self.use_spi:
                                    self.strip.set_led_rgb_data(i+q, self.color)
                                else:
                                    self.strip.setPixelColor(i+q, Color(self.color[0], self.color[1], self.color[2]))
                        self.strip.show()
                        await asyncio.sleep(0.1)
                        for i in range(0, num_pixels, 3):
                            if i+q < num_pixels:
                                if self.use_spi:
                                    self.strip.set_led_rgb_data(i+q, (0,0,0))
                                else:
                                    self.strip.setPixelColor(i+q, Color(0,0,0))

                elif self.mode == "strobe":
                    self._set_color(self.color)
                    await asyncio.sleep(0.05)
                    self._set_color((0,0,0))
                    await asyncio.sleep(0.05)

                elif self.mode == "twinkle":
                    self._set_color((0,0,0))
                    idx = random.randint(0, num_pixels-1)
                    if self.use_spi:
                        self.strip.set_led_rgb_data(idx, self.color)
                    else:
                        self.strip.setPixelColor(idx, Color(self.color[0], self.color[1], self.color[2]))
                    self.strip.show()
                    await asyncio.sleep(0.1)

                elif self.mode == "sparkle":
                    self._set_color(self.color)
                    idx = random.randint(0, num_pixels-1)
                    if self.use_spi:
                        self.strip.set_led_rgb_data(idx, (255,255,255))
                    else:
                        self.strip.setPixelColor(idx, Color(255,255,255))
                    self.strip.show()
                    await asyncio.sleep(0.05)

                elif self.mode == "solid_rainbow":
                    for j in range(256):
                        if self.mode != "solid_rainbow": break
                        c = self._wheel_tuple(j)
                        self._set_color(c)
                        await asyncio.sleep(0.05)

                elif self.mode == "confetti":
                    self._set_color((0,0,0))
                    idx = random.randint(0, num_pixels-1)
                    c = self._wheel_tuple(random.randint(0, 255))
                    if self.use_spi:
                        self.strip.set_led_rgb_data(idx, c)
                    else:
                        self.strip.setPixelColor(idx, Color(c[0], c[1], c[2]))
                    self.strip.show()
                    await asyncio.sleep(0.1)

                elif self.mode == "sinelon":
                    for i in range(num_pixels):
                        if self.mode != "sinelon": break
                        self._set_color((0,0,0))
                        if self.use_spi:
                            self.strip.set_led_rgb_data(i, self.color)
                        else:
                            self.strip.setPixelColor(i, Color(self.color[0], self.color[1], self.color[2]))
                        self.strip.show()
                        await asyncio.sleep(0.1)
                    for i in range(num_pixels-1, -1, -1):
                        if self.mode != "sinelon": break
                        self._set_color((0,0,0))
                        if self.use_spi:
                            self.strip.set_led_rgb_data(i, self.color)
                        else:
                            self.strip.setPixelColor(i, Color(self.color[0], self.color[1], self.color[2]))
                        self.strip.show()
                        await asyncio.sleep(0.1)

                elif self.mode == "bpm":
                    for i in range(0, 256, 20):
                        if self.mode != "bpm": break
                        factor = i / 255.0
                        c = (int(self.color[0] * factor), int(self.color[1] * factor), int(self.color[2] * factor))
                        self._set_color(c)
                        await asyncio.sleep(0.01)
                    for i in range(255, -1, -20):
                        if self.mode != "bpm": break
                        factor = i / 255.0
                        c = (int(self.color[0] * factor), int(self.color[1] * factor), int(self.color[2] * factor))
                        self._set_color(c)
                        await asyncio.sleep(0.01)

                elif self.mode == "juggle":
                    self._set_color((0,0,0))
                    t = time.time()
                    i1 = int((1 +  (t * 2) % (num_pixels-1)))
                    i2 = int((1 +  (t * 3) % (num_pixels-1)))
                    c1 = self.color
                    c2 = (255 - self.color[0], 255 - self.color[1], 255 - self.color[2])
                    if self.use_spi:
                        self.strip.set_led_rgb_data(i1 % num_pixels, c1)
                        self.strip.set_led_rgb_data(i2 % num_pixels, c2)
                    else:
                        self.strip.setPixelColor(i1 % num_pixels, Color(c1[0], c1[1], c1[2]))
                        self.strip.setPixelColor(i2 % num_pixels, Color(c2[0], c2[1], c2[2]))
                    self.strip.show()
                    await asyncio.sleep(0.1)

                elif self.mode == "running_lights":
                    t = time.time() * 2
                    colors = []
                    for i in range(num_pixels):
                        val = int(((numpy.sin(i + t) + 1) / 2) * 255) if 'numpy' in globals() else 128
                        # Simplified without numpy for now
                        val = int((1 + (i/2.0 + t)) % 2 * 128)
                        colors.append((val, 0, 0))
                    self._set_pixels(colors)
                    await asyncio.sleep(0.05)

                elif self.mode == "meteor":
                    self._set_color((0,0,0))
                    for i in range(num_pixels):
                        if self.mode != "meteor": break
                        self._set_color((0,0,0))
                        if self.use_spi:
                            self.strip.set_led_rgb_data(i, (255, 255, 255))
                        else:
                            self.strip.setPixelColor(i, Color(255, 255, 255))
                        self.strip.show()
                        await asyncio.sleep(0.05)

                elif self.mode == "snow":
                    idx = random.randint(0, num_pixels-1)
                    if self.use_spi:
                        self.strip.set_led_rgb_data(idx, (255, 255, 255))
                    else:
                        self.strip.setPixelColor(idx, Color(255, 255, 255))
                    self.strip.show()
                    await asyncio.sleep(0.1)
                    if random.random() > 0.5:
                        idx_clear = random.randint(0, num_pixels-1)
                        if self.use_spi:
                            self.strip.set_led_rgb_data(idx_clear, (0,0,0))
                        else:
                            self.strip.setPixelColor(idx_clear, Color(0,0,0))
                        self.strip.show()

                elif self.mode == "halloween":
                    colors = []
                    for i in range(num_pixels):
                        if i % 2 == 0:
                            colors.append((255, 140, 0))
                        else:
                            colors.append((128, 0, 128))
                    self._set_pixels(colors)
                    await asyncio.sleep(0.5)
                    colors = []
                    for i in range(num_pixels):
                        if i % 2 != 0:
                            colors.append((255, 140, 0))
                        else:
                            colors.append((128, 0, 128))
                    self._set_pixels(colors)
                    await asyncio.sleep(0.5)

                elif self.mode == "christmas":
                    colors = []
                    for i in range(num_pixels):
                        if i % 2 == 0:
                            colors.append((255, 0, 0))
                        else:
                            colors.append((0, 255, 0))
                    self._set_pixels(colors)
                    await asyncio.sleep(0.5)
                    colors = []
                    for i in range(num_pixels):
                        if i % 2 != 0:
                            colors.append((255, 0, 0))
                        else:
                            colors.append((0, 255, 0))
                    self._set_pixels(colors)
                    await asyncio.sleep(0.5)

                elif self.mode == "usa":
                    pattern = [(255,0,0), (255,255,255), (0,0,255)]
                    colors = [pattern[i % 3] for i in range(num_pixels)]
                    self._set_pixels(colors)
                    await asyncio.sleep(0.2)
                    pattern = [(0,0,255), (255,0,0), (255,255,255)]
                    colors = [pattern[i % 3] for i in range(num_pixels)]
                    self._set_pixels(colors)
                    await asyncio.sleep(0.2)

                elif self.mode == "matrix":
                    self._set_color((0,0,0))
                    idx = random.randint(0, num_pixels-1)
                    if self.use_spi:
                        self.strip.set_led_rgb_data(idx, (0, 255, 0))
                    else:
                        self.strip.setPixelColor(idx, Color(0, 255, 0))
                    self.strip.show()
                    await asyncio.sleep(0.05)

                elif self.mode == "mood":
                    for j in range(256):
                        if self.mode != "mood": break
                        c = self._wheel_tuple(j)
                        self._set_color(c)
                        await asyncio.sleep(0.2)

                elif self.mode == "heartbeat":
                    self._set_color((255, 0, 0))
                    await asyncio.sleep(0.1)
                    self._set_color((0, 0, 0))
                    await asyncio.sleep(0.1)
                    self._set_color((255, 0, 0))
                    await asyncio.sleep(0.1)
                    self._set_color((0, 0, 0))
                    await asyncio.sleep(0.8)

                elif self.mode == "disco":
                    colors = []
                    for _ in range(num_pixels):
                        c = self._wheel_tuple(random.randint(0, 255))
                        colors.append(c)
                    self._set_pixels(colors)
                    await asyncio.sleep(0.1)

                else:
                    await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Animation error: {e}")
                await asyncio.sleep(1)

    def _wheel(self, pos):
        """Generate rainbow colors (int for NeoPixel)"""
        if pos < 85:
            return Color(pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return Color(255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return Color(0, pos * 3, 255 - pos * 3)

    def _wheel_tuple(self, pos):
        """Generate rainbow colors (tuple for SPI)"""
        if pos < 85:
            return (pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return (255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return (0, pos * 3, 255 - pos * 3)
