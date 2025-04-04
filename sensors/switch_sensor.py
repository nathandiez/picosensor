# switch_sensor.py

import machine

class SwitchSensor:

    def __init__(self, config):
        pin_num = config.get("PIN", 15)
        self.pin = machine.Pin(pin_num, machine.Pin.IN, machine.Pin.PULL_DOWN)

    def read(self):
        state = "HIGH" if self.pin.value() == 1 else "LOW"
        return state
