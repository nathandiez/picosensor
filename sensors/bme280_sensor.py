import machine
import time
from lib.sensors.bme280 import BME280


class BME280Sensor:
    def __init__(self, config):
        scl_pin = config.get("i2c_scl")
        sda_pin = config.get("i2c_sda")

        print(
            f"########### BME280 DEBUG: Initializing with SCL pin {scl_pin}, SDA pin {sda_pin}"
        )

        self.i2c = machine.I2C(0, scl=machine.Pin(scl_pin), sda=machine.Pin(sda_pin))

        # Debug: Scan for I2C devices
        print("BME280 DEBUG: Scanning I2C bus...")
        devices = self.i2c.scan()
        print(f"BME280 DEBUG: Found I2C devices: {[hex(addr) for addr in devices]}")

        # Check for BME280 at expected addresses
        bme_addresses = [0x76, 0x77]
        found_addresses = [addr for addr in devices if addr in bme_addresses]
        if found_addresses:
            print(
                f"BME280 DEBUG: BME280 detected at address(es): {[hex(addr) for addr in found_addresses]}"
            )
        else:
            print(
                f"BME280 DEBUG: WARNING - No BME280 found at expected addresses {[hex(addr) for addr in bme_addresses]}"
            )

        print("BME280 DEBUG: Creating BME280 sensor object...")
        self.sensor = BME280(i2c=self.i2c)
        print("BME280 DEBUG: BME280 sensor object created successfully")

        # Give sensor time to stabilize
        time.sleep(0.1)

        # Test initial read
        print("BME280 DEBUG: Performing initial test read...")
        try:
            test_values = self.sensor.values
            print(f"BME280 DEBUG: Initial test read result: {test_values}")
            print(
                f"BME280 DEBUG: Test read types: {[type(v) for v in test_values] if test_values else 'None'}"
            )
        except Exception as e:
            print(f"BME280 DEBUG: Error during initial test read: {e}")

    def read_values(self):
        # Returns values as (temperature_f, humidity, pressure_inhg)
        print("############# BME280 DEBUG: Starting read_values()")

        try:
            # Get raw values from sensor
            print("BME280 DEBUG: Calling self.sensor.values...")
            raw_values = self.sensor.values
            print(f"BME280 DEBUG: Raw values returned: {raw_values}")
            print(f"BME280 DEBUG: Raw values type: {type(raw_values)}")

            if raw_values is None:
                print("BME280 DEBUG: ERROR - sensor.values returned None")
                return None, None, None

            if not isinstance(raw_values, (tuple, list)) or len(raw_values) != 3:
                print(
                    f"BME280 DEBUG: ERROR - Expected tuple/list of 3 values, got: {raw_values}"
                )
                return None, None, None

            temp_str, hum_str, press_str = raw_values
            print(f"BME280 DEBUG: Unpacked values:")
            print(f"  Temperature: '{temp_str}' (type: {type(temp_str)})")
            print(f"  Humidity: '{hum_str}' (type: {type(hum_str)})")
            print(f"  Pressure: '{press_str}' (type: {type(press_str)})")

            # Check for None values
            if temp_str is None or hum_str is None or press_str is None:
                print(f"BME280 DEBUG: ERROR - One or more values is None")
                print(f"  temp_str: {temp_str}")
                print(f"  hum_str: {hum_str}")
                print(f"  press_str: {press_str}")
                return None, None, None

            # Try to parse each value
            print("BME280 DEBUG: Parsing temperature...")
            try:
                temp_clean = str(temp_str).replace("C", "").strip()
                print(f"BME280 DEBUG: Temperature after cleaning: '{temp_clean}'")
                temp_f = float(temp_clean)
                print(f"BME280 DEBUG: Temperature (already in Fahrenheit): {temp_f}°F")
            except Exception as e:
                print(f"BME280 DEBUG: ERROR parsing temperature: {e}")
                temp_f = None

            print("BME280 DEBUG: Parsing humidity...")
            try:
                hum_clean = str(hum_str).replace("%", "").strip()
                print(f"BME280 DEBUG: Humidity after cleaning: '{hum_clean}'")
                humidity = float(hum_clean)
                print(f"BME280 DEBUG: Humidity parsed: {humidity}%")
            except Exception as e:
                print(f"BME280 DEBUG: ERROR parsing humidity: {e}")
                humidity = None

            print("BME280 DEBUG: Parsing pressure...")
            try:
                press_clean = str(press_str).replace("hPa", "").strip()
                print(f"BME280 DEBUG: Pressure after cleaning: '{press_clean}'")
                pressure_hpa = float(press_clean)
                pressure_inhg = pressure_hpa * 0.02953  # Convert hPa to inHg
                print(
                    f"BME280 DEBUG: Pressure conversion: {pressure_hpa} hPa → {pressure_inhg} inHg"
                )
            except Exception as e:
                print(f"BME280 DEBUG: ERROR parsing pressure: {e}")
                pressure_inhg = None

            print(
                f"BME280 DEBUG: Final values: temp_f={temp_f}, humidity={humidity}, pressure_inhg={pressure_inhg}"
            )
            return temp_f, humidity, pressure_inhg

        except Exception as e:
            print(f"BME280 DEBUG: CRITICAL ERROR in read_values(): {e}")
            print(f"BME280 DEBUG: Exception type: {type(e)}")
            try:
                print(f"BME280 DEBUG: Current sensor.values: {self.sensor.values}")
            except:
                print("BME280 DEBUG: Cannot read sensor.values due to error")

            # Print full traceback
            import sys

            print("BME280 DEBUG: Full traceback:")
            sys.print_exception(e)

            return None, None, None