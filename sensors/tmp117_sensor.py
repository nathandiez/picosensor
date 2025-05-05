# tmp117_sensor.py
import machine
import time


class TMP117Sensor:
    def __init__(self, config):
        scl_pin = config.get("i2c_scl")
        sda_pin = config.get("i2c_sda")
        self.i2c = machine.I2C(0, scl=machine.Pin(scl_pin), sda=machine.Pin(sda_pin))
        self.addr = 0x48  # Default I2C address for TMP117
        if self.addr not in self.i2c.scan():
            raise RuntimeError("TMP117 sensor not found")

        # Register addresses
        self.TEMP_REG = 0x00  # Temperature register
        self.CONFIG_REG = 0x01  # Configuration register

        # Configure for continuous conversion mode
        self.i2c.writeto_mem(self.addr, self.CONFIG_REG, b"\x02\x00")
        time.sleep_ms(100)  # Wait for configuration to apply

    def read_values(self):
        # Read the temperature register (2 bytes)
        data = self.i2c.readfrom_mem(self.addr, self.TEMP_REG, 2)

        # Convert the raw value (signed 16-bit integer)
        raw_temp = (data[0] << 8) | data[1]
        if raw_temp > 32767:
            raw_temp -= 65536  # Handle negative values (two's complement)

        # TMP117 has a resolution of 0.0078125C (7.8125 milli-degrees)
        temperature_c = raw_temp * 0.0078125
        temperature_f = temperature_c * 9 / 5 + 32

        return temperature_f
