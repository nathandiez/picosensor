# oledtest.py - Test script for font capabilities
from displays.OLED1306Manager import OLED1306Display
import time
import sys  # Add this import for the exit() function

print("Creating OLED display instance...")
oled = OLED1306Display()

# Check if display initialized correctly
if not oled.is_initialized():
    print("OLED display not found or failed to initialize")
    sys.exit(1)  # Use sys.exit instead of exit

print("Display initialized successfully")

# Test standard font
print("Testing standard font...")
oled.clear()
oled.text("Standard Font", 0, 0)
oled.text("8x8 pixels", 0, 10)
oled.show()
time.sleep(2)

# Initialize fonts
print("Initializing custom fonts...")
if not oled.init_fonts():
    print("Failed to initialize fonts. Check if font files exist in lib directory.")
    sys.exit(1)  # Use sys.exit instead of exit

# Test sans serif font
print("Testing sans serif font...")
oled.clear()
oled.text_new("Sans 20px", 0, 20, font="sans")
time.sleep(2)

# Test small font (font14)
print("Testing small font...")
oled.clear()
oled.text_new("Small Font Test", 0, 20, font="small")

time.sleep(2)

# Test monospace font
print("Testing monospace font...")
oled.clear()
oled.text_new("Mono 20", 0, 20, font="mono")
time.sleep(2)

# Test mixed font usage
print("Testing mixed fonts...")
oled.clear()
oled.text("Standard Font", 0, 0)
oled.text_new("26.7C", 20, 20, font="sans")
oled.text("Temperature", 0, 50)
time.sleep(2)

# Test big headline
print("Testing big headline...")
oled.clear()
oled.topline("Weather", 1, font="sans")
oled.text("Temperature: 26.7C", 0, 30)
oled.text("Humidity: 45%", 0, 40)
oled.text("Pressure: 1013hPa", 0, 50)
time.sleep(2)

print("Testing font comparison...")
oled.clear()

# Title
oled.text("Font Comparison:", 0, 0)
oled.show()
time.sleep(1)

# Standard 8-pixel font
test_string = "12345678901234567890"
oled.text("Standard:", 0, 15)
oled.text(test_string, 0, 25)

# font14 (small font)
oled.text("font14:", 0, 40)
oled.text_new(test_string, 0, 50, font="small")

oled.show()
time.sleep(5) 

# Test comparison between built-in font and DejaVu Sans Condensed
print("Testing condensed font comparison...")
oled.clear()

# Title
oled.text("Font Comparison:", 0, 0)
oled.show()
time.sleep(1)

# Test string
test_string = "12345678901234567890"

# Standard 8-pixel font
oled.text("Standard:", 0, 15)
oled.text(test_string, 0, 25)

# DejaVu Sans Condensed font
oled.text("Condensed:", 0, 40)
oled.text_new(test_string, 0, 50, font="small")

oled.show()
time.sleep(5)  # Give more time to observe the difference


# Done
print("Test complete")
oled.clear()
oled.text("Font Test", 0, 0)
oled.text("Complete!", 0, 10)
oled.show()