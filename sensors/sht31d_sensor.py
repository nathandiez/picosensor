# sht31d_sensor.py
import machine
import time


class SHT31DSensor:
    def __init__(self, config):
        scl_pin = config.get("i2c_scl")
        sda_pin = config.get("i2c_sda")
        self.i2c = machine.I2C(0, scl=machine.Pin(scl_pin), sda=machine.Pin(sda_pin))
        self.addr = 0x44
        if self.addr not in self.i2c.scan():
            raise RuntimeError("SHT31D sensor not found")

    def read_values(self):
        # High repeatability measurement command
        self.i2c.writeto(self.addr, b"\x24\x00")
        time.sleep_ms(15)
        data = self.i2c.readfrom(self.addr, 6)

        # Raw values
        raw_temp = data[0] << 8 | data[1]
        raw_hum = data[3] << 8 | data[4]

        # Conversion formulas
        temperature_c = -45 + (175 * raw_temp / 65535)
        temperature_f = temperature_c * 9 / 5 + 32
        humidity = 100 * raw_hum / 65535

        return temperature_f, humidity
