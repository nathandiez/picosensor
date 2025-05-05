# oledtinyfonttest.py
from displays.OLED1306Manager import OLED1306Display
import time, sys

oled = OLED1306Display()
if not oled.is_initialized():
    print("No OLED")
    sys.exit(1)

# init your writers
if not oled.init_fonts():
    print("Font init failed")
    sys.exit(1)

test_string = "12345678901234567890"

oled.clear()
# 1) Built‑in 8 px text
oled.text("Std 8‑px:",   0,  0)
oled.text(test_string,   0, 10)

# 2) DejaVu 8‑px
oled.text("dejavu8:",    0, 20)
# since the font is 8 px tall, start it at y=28
oled.text_new(test_string, 0, 28, font="dejavu8")

oled.text("dejavu9:",    0, 38)
oled.text_new(test_string, 0, 46, font="dejavu9")

oled.show()
time.sleep(5)
