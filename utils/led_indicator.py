# utils/led_indicator.py
import machine
import time

class LEDIndicator:
    def __init__(self, pin="LED", inverted=True):
        """
        Initialize LED indicator
        - pin: LED pin (use "LED" for onboard LED on Pico W)
        - inverted: Set to True for Pico W onboard LED which is active LOW
        """
        # "LED" is a special pin name for the onboard LED on Pico W
        if pin == "LED":
            self.led = machine.Pin("LED", machine.Pin.OUT)
        else:
            self.led = machine.Pin(pin, machine.Pin.OUT)
        
        self.inverted = inverted
        self.enabled = False
        self.last_toggle_time = 0
        self.interval_ms = 1000
        self.state = False  # Current logical state
        
        # Ensure LED is off initially
        self._set_led(False)
    
    def _set_led(self, state):
        """Set LED state with inverted logic if needed"""
        if self.inverted:
            self.led.value(not state)
        else:
            self.led.value(state)
        self.state = state
    
    def start(self, interval_ms=1000):
        """Enable LED blinking"""
        self.enabled = True
        self.interval_ms = interval_ms
        self.last_toggle_time = time.ticks_ms()  # Start immediately
    
    def stop(self):
        """Disable LED blinking and turn off LED"""
        self.enabled = False
        self._set_led(False)
    
    def update(self):
        """
        Update LED state based on current time
        Returns True if LED was toggled
        """
        if not self.enabled:
            return False
            
        current_time = time.ticks_ms()
        
        # Check if it's time to toggle the LED
        if time.ticks_diff(current_time, self.last_toggle_time) >= self.interval_ms:
            # Toggle LED
            self._set_led(not self.state)
            self.last_toggle_time = current_time
            return True
            
        return False