# OLED1306Manager.py
from machine import Pin, SoftI2C
import time
import gc
from lib.oled1306.ssd1306 import SSD1306_I2C


class OLED1306Display:
    def __init__(self):
        self.i2c_id = 0
        self.sda_pin = 20
        self.scl_pin = 21
        self.width = 128
        self.height = 64
        self.addr = 60

        # Status rows for display
        self.strows = [
            "",
            "",
            "",
        ]

        # Initialize the display
        self.oled = self._init_display()

        # Initialize fonts (but don't import unless needed)
        self._writer_module = None
        self._writer_class = None
        self.writer_sans = None
        self.writer_mono = None
        self.writer_ptsans8 = None
        self.writer_dejavu8 = None
        self.writer_dejavu9 = None
        self.writer_dejavu18 = None

    def _init_display(self):
        """
        Initialize the OLED display using SoftI2C directly.
        Returns an SSD1306_I2C instance or None on failure.
        """
        import time
        from machine import Pin, SoftI2C

        # --- 1) Deinit any leftover I2C (in case it exists) ---
        print("    Deinitializing I2C")
        try:
            self.i2c.deinit()
        except Exception:
            pass

        # --- 2) Bus recovery via open-drain bit-bang ---
        print("    Recovering I2C bus")
        sda = Pin(self.sda_pin, Pin.OPEN_DRAIN, value=1)
        scl = Pin(self.scl_pin, Pin.OPEN_DRAIN, value=1)
        for _ in range(9):
            scl.value(0)
            time.sleep_us(10)
            scl.value(1)
            time.sleep_us(10)
        # STOP condition
        sda.value(0)
        time.sleep_us(10)
        scl.value(1)
        time.sleep_us(10)
        sda.value(1)
        time.sleep_us(10)
        time.sleep_ms(50)

        # --- 3) Use SoftI2C directly ---
        try:
            print("    Using SoftI2C for OLED")
            self.i2c = SoftI2C(scl=scl, sda=sda, freq=200_000)
            devs = self.i2c.scan()
            print("    SoftI2C devices:", [hex(d) for d in devs])
            if self.addr in devs:
                print(f"    OLED found at 0x{self.addr:02X} (SoftI2C)")
                oled = SSD1306_I2C(self.width, self.height, self.i2c, self.addr)
                oled.init_display()
                oled.fill(0)
                # oled.text("OLED init OK", 0, 0)
                oled.show()
                # time.sleep_ms(500)
                oled.fill(0)
                oled.show()
                return oled
        except Exception as e:
            print(f"    SoftI2C SSD1306 init failed: {e}")

        # --- Attempt failed ---
        print("    OLED init failed")
        return None

    def init_fonts(self):
        """Initialize font writers"""
        if not self.is_initialized():
            return False

        try:
            # Import the required modules with updated paths
            print("Importing writer module...")
            self._writer_module = __import__(
                "lib.oled1306.writer", globals(), locals(), ["Writer"], 0
            )
            self._writer_class = self._writer_module.Writer

            # Import font modules with updated paths
            print("Importing font modules...")
            freesans_module = __import__(
                "lib.oled1306.freesans20", globals(), locals(), ["freesans20"], 0
            )
            courier_module = __import__(
                "lib.oled1306.courier20", globals(), locals(), ["courier20"], 0
            )
            dejavu_small_module = __import__(
                "lib.oled1306.dejavu_sans_condensed_6",
                globals(),
                locals(),
                ["dejavu_sans_condensed_6"],
                0,
            )
            font14_module = __import__(
                "lib.oled1306.font14", globals(), locals(), ["font14"], 0
            )
            dejavu8_module = __import__(
                "lib.oled1306.dejavu_sans_condensed_8",
                globals(),
                locals(),
                ["dejavu_sans_condensed_8"],
                0,
            )
            dejavu9_module = __import__(
                "lib.oled1306.dejavu_9", globals(), locals(), ["dejavu_9"], 0
            )
            dejavu18_module = __import__(
                "lib.oled1306.dejavu_18", globals(), locals(), ["dejavu_18"], 0
            )
            ptsans8_module = __import__(
                "lib.oled1306.ptsansnarrow_8",
                globals(),
                locals(),
                ["ptsansnarrow_8"],
                0,
            )

            # Create writer instances
            print("Creating writer instances...")
            self.writer_sans = self._writer_class(self.oled, freesans_module)
            self.writer_mono = self._writer_class(self.oled, courier_module)
            self.writer_small = self._writer_class(self.oled, dejavu_small_module)
            self.writer_font14 = self._writer_class(
                self.oled, font14_module
            )  # Add this line
            self.writer_dejavu = self.writer_small
            self.writer_dejavu8 = self._writer_class(self.oled, dejavu8_module)
            self.writer_dejavu9 = self._writer_class(self.oled, dejavu9_module)
            self.writer_dejavu18 = self._writer_class(self.oled, dejavu18_module)
            self.writer_ptsans8 = self._writer_class(self.oled, ptsans8_module)

            print("Font initialization complete")
            return True
        except ImportError as e:
            print(f"Font import error: {e}")
            return False
        except Exception as e:
            print(f"Font initialization error: {e}")
            return False

    def is_initialized(self):
        """Check if the OLED display is initialized"""
        return self.oled is not None

    def log(self, text):
        """Fast 3‑line scrolllog using 9px Dejavu font."""
        if not self.is_initialized():
            return False

        # 1) Manage a small ring buffer
        if not hasattr(self, "log_rows"):
            self.log_rows = [""] * 3
        self.log_rows.pop(0)
        self.log_rows.append(text)

        # 2) Clear bottom region in one call
        divider_y = 32
        self.oled.fill_rect(0, divider_y, self.width, self.height - divider_y, 0)

        # 3) Ensure font writers are loaded
        if self._writer_class is None:
            if not self.init_fonts():
                return False

        # 4) Blit each line (9px high) without calling show()
        for i, row in enumerate(self.log_rows):
            y = divider_y + i * 9
            self._writer_class.set_textpos(self.oled, y, 0)
            self.writer_dejavu9.printstring(row)

        # 5) Push one frame update
        self.oled.show()
        # time.sleep_ms(100)  # Optional delay for smoother scrolling
        return True

    def clear(self):
        """Clear the OLED display"""
        if not self.is_initialized():
            return False

        self.oled.fill(0)
        self.oled.show()
        self.strows = ["", "", ""]
        return True

    def blink(self):
        """Blink a small indicator on the OLED display"""
        if not self.is_initialized():
            return False

        # Draw a small indicator
        self.oled.hline(63, 59, 3, 1)
        self.oled.hline(63, 60, 3, 1)
        self.oled.hline(63, 61, 3, 1)
        self.oled.show()
        time.sleep_ms(100)

        # Clear the indicator
        self.oled.hline(63, 59, 3, 0)
        self.oled.hline(63, 60, 3, 0)
        self.oled.hline(63, 61, 3, 0)
        self.oled.show()
        return True

    def power_off(self):
        """Turn off the OLED display"""
        if self.is_initialized():
            self.oled.poweroff()
            return True
        return False

    def power_on(self):
        """Turn on the OLED display"""
        if self.is_initialized():
            self.oled.poweron()
            return True
        return False

    def set_contrast(self, contrast):
        """Set the contrast of the OLED display (0-255)"""
        if self.is_initialized():
            self.oled.contrast(contrast)
            return True
        return False

    def invert(self, invert=True):
        """Invert the colors of the OLED display"""
        if self.is_initialized():
            self.oled.invert(invert)
            return True
        return False

    def rotate(self, rotate=True):
        """Rotate the display 180 degrees"""
        if self.is_initialized():
            self.oled.rotate(rotate)
            return True
        return False

    def text(self, text, x, y):
        """Draw text at the specified position"""
        if self.is_initialized():
            self.oled.text(text, x, y)
            return True
        return False

    def fill(self, color):
        """Fill the entire display with the specified color (0 or 1)"""
        if self.is_initialized():
            self.oled.fill(color)
            return True
        return False

    def pixel(self, x, y, color):
        """Set a pixel at the specified position to the specified color"""
        if self.is_initialized():
            self.oled.pixel(x, y, color)
            return True
        return False

    def hline(self, x, y, w, color):
        """Draw a horizontal line"""
        if self.is_initialized():
            self.oled.hline(x, y, w, color)
            return True
        return False

    def vline(self, x, y, h, color):
        """Draw a vertical line"""
        if self.is_initialized():
            self.oled.vline(x, y, h, color)
            return True
        return False

    def line(self, x1, y1, x2, y2, color):
        """Draw a line from (x1,y1) to (x2,y2)"""
        if self.is_initialized():
            self.oled.line(x1, y1, x2, y2, color)
            return True
        return False

    def rect(self, x, y, w, h, color):
        """Draw a rectangle"""
        if self.is_initialized():
            self.oled.rect(x, y, w, h, color)
            return True
        return False

    def fill_rect(self, x, y, w, h, color):
        """Draw a filled rectangle"""
        if self.is_initialized():
            self.oled.fill_rect(x, y, w, h, color)
            return True
        return False

    def show(self):
        """Update the display with the current buffer contents"""
        if self.is_initialized():
            self.oled.show()
            return True
        return False

    def text_row(
        self, text, row
    ):  # displays text starting at a specific row based on an 8 pixel font
        if not self.is_initialized():
            return False

        if row not in range(1, 8):
            print(f"Invalid row: {row}. Must be 1 through 7.")
            return False

        y_position = (row - 1) * 8
        self.oled.fill_rect(0, y_position, self.width, 8, 0)
        self.oled.text(text[:16], 0, y_position)  # Limit to 16 chars to fit on screen
        self.oled.show()

    # New methods for working with larger fonts
    def text_new(self, text, x, y, font="sans", clear_first=False):
        """
        Display text in a large font

        Args:
            text: Text to display
            x, y: Position on screen
            font: "sans", "mono", or "small" font
            clear_first: Whether to clear the screen first
        """
        if not self.is_initialized():
            return False

        # Initialize fonts if not already done
        if self._writer_class is None:
            if not self.init_fonts():
                return False

        # Clear screen if requested
        if clear_first:
            self.oled.fill(0)

        # Choose font
        if font == "sans":
            writer = self.writer_sans
        elif font == "mono":
            writer = self.writer_mono
        elif font == "font14":
            writer = self.writer_font14
        elif font == "dejavu8":
            writer = self.writer_dejavu8
        elif font == "dejavu9":
            writer = self.writer_dejavu9
        elif font == "ptsans8":
            writer = self.writer_ptsans8
        elif font == "dejavu":
            writer = self.writer_dejavu
        else:
            writer = self.writer_sans  # Default

        # Set position and print
        self._writer_class.set_textpos(self.oled, y, x)
        writer.printstring(text)
        self.oled.show()
        return True

    def bigline1(self, text):
        if not self.is_initialized():
            return False

        # 1) Clear the top 20px
        self.oled.fill_rect(0, 0, self.width, 16, 0)

        # 2) Ensure font writers are ready
        if self._writer_class is None:
            if not self.init_fonts():
                return False

        # 3) Position at (row=0, col=0) and print
        self._writer_class.set_textpos(self.oled, 0, 0)
        self.writer_font14.printstring(text)

        # 4) Push one frame
        self.oled.show()
        return True

    def bigline2(self, text):
        if not self.is_initialized():
            return False

        # 1) Clear the top 20px
        self.oled.fill_rect(0, 16, self.width, 16, 0)

        # 2) Ensure font writers are ready
        if self._writer_class is None:
            if not self.init_fonts():
                return False

        # 3) Position at (row=0, col=0) and print
        self._writer_class.set_textpos(self.oled, 16, 0)
        self.writer_font14.printstring(text)

        # 4) Push one frame
        self.oled.show()
        return True

    def deinit(self):
        """Clean up OLED display resources before shutdown"""
        if not self.is_initialized():
            return False

        try:
            # Clear the display first
            self.oled.fill(0)
            self.oled.show()

            # Power off the display
            self.oled.poweroff()

            # Deinitialize the I2C bus if it exists
            if hasattr(self, "i2c") and self.i2c:
                try:
                    self.i2c.deinit()
                except AttributeError:
                    # SoftI2C might not have deinit in some MicroPython versions
                    pass

            # Set display object to None to indicate it's deinitialized
            self.oled = None

            # Free memory with garbage collection
            gc.collect()

            return True
        except Exception as e:
            print(f"OLED deinit error: {e}")
            return False
