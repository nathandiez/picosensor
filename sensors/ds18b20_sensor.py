# ds18b20_sensor.py

import machine
import time
import onewire
import ds18x20


class DS18B20Sensor:
    def __init__(self, config):
        # Get the pin number directly from the configuration structure
        # This matches the pattern used in MotionSensor class
        pin_num = config.get("pin")

        if pin_num is None:
            raise ValueError("Missing onewire data pin configuration")

        # Initialize the 1-Wire bus on the specified pin
        self.data_pin = machine.Pin(pin_num)
        self.onewire_bus = onewire.OneWire(self.data_pin)

        # Initialize the DS18X20 temperature sensor
        self.sensor = ds18x20.DS18X20(self.onewire_bus)

        # Scan for devices on the bus
        self.roms = self.sensor.scan()
        if not self.roms:
            raise RuntimeError("No DS18B20 sensors found on 1-Wire bus")

        print(f"Found {len(self.roms)} DS18B20 sensors")

    def read_values(self):
        try:
            # Start temperature conversion on all sensors
            self.sensor.convert_temp()

            # DS18B20 requires at least 750ms for conversion
            time.sleep_ms(750)

            # Read temperature from the first sensor found (in Celsius)
            # For multiple sensors, you could return a list of temperatures
            temperature_c = self.sensor.read_temp(self.roms[0])

            # Convert to Fahrenheit
            temperature_f = temperature_c * 9 / 5 + 32

            return temperature_f

        except Exception as e:
            print(f"Error reading DS18B20 sensor: {e}")
            return None
