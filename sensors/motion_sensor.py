# motion_sensor.py

import machine


class MotionSensor:

    def __init__(self, config):
        pin_num = config.get("pin")
        self.pin = machine.Pin(pin_num, machine.Pin.IN, machine.Pin.PULL_DOWN)

    def read(self):
        state = "HIGH" if self.pin.value() == 1 else "LOW"
        return state
