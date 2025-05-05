# bme280_sensor.py
import machine
from lib.sensors.bme280 import BME280


class BME280Sensor:
    def __init__(self, config):
        scl_pin = config.get("i2c_scl")
        sda_pin = config.get("i2c_sda")
        self.i2c = machine.I2C(0, scl=machine.Pin(scl_pin), sda=machine.Pin(sda_pin))
        self.sensor = BME280(i2c=self.i2c)

    def read_values(self):
        # Returns values as (temperature_f, humidity, pressure_inhg)
        t, h, p = self.sensor.values
        return t, h, p
