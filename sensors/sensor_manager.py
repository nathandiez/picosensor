# sensor_manager.py

from sensors.bme280_sensor import BME280Sensor
from sensors.sht31d_sensor import SHT31DSensor
from sensors.tmp117_sensor import TMP117Sensor
from sensors.ds18b20_sensor import DS18B20Sensor
from sensors.internal_temp_sensor import InternalTempSensor
from sensors.motion_sensor import MotionSensor
from sensors.switch_sensor import SwitchSensor


class SensorManager:
    def __init__(
        self,
        i2c_temp_sensor_pins,
        motion_sensor_pin,
        switch_sensor_pin,
        onewire_ds18b20_pin,
    ):
        self.i2c_temp_sensor_pins = i2c_temp_sensor_pins
        self.motion_sensor_pin = motion_sensor_pin
        self.switch_sensor_pin = switch_sensor_pin
        # The missing line - store onewire_ds18b20_pin as an instance attribute
        self.onewire_ds18b20_pin = onewire_ds18b20_pin

        self.temp_sensor = None
        self.motion_sensor = None
        self.switch_sensor = None

        self.previous_motion_state = None
        self.previous_switch_state = None

    def initialize_sensors(self):
        try:
            # Initialize temperature sensor (tries different types in order)
            self._initialize_temp_sensor()

            # Initialize motion and switch sensors
            self.motion_sensor = MotionSensor(self.motion_sensor_pin)
            self.switch_sensor = SwitchSensor(self.switch_sensor_pin)

            # Get initial states
            self.previous_motion_state = self.motion_sensor.read()
            self.previous_switch_state = self.switch_sensor.read()

            print(
                f"Initial Motion: {self.previous_motion_state}, Initial Switch: {self.previous_switch_state}"
            )
            return True

        except Exception as e:
            print(f"Sensor initialization failed: {e}")
            return False

    def _initialize_temp_sensor(self):
        try:
            self.temp_sensor = BME280Sensor(self.i2c_temp_sensor_pins)
            print("Using BME280 sensor.")
            return
        except Exception as e1:
            print(f"BME280 not found: {e1}")

        try:
            self.temp_sensor = SHT31DSensor(self.i2c_temp_sensor_pins)
            print("Using SHT31D sensor.")
            return
        except Exception as e2:
            print(f"SHT31D not found: {e2}")

        try:
            self.temp_sensor = TMP117Sensor(self.i2c_temp_sensor_pins)
            print("Using TMP117 sensor.")
            return
        except Exception as e3:
            print(f"TMP117 not found: {e3}")

        try:
            self.temp_sensor = DS18B20Sensor(self.onewire_ds18b20_pin)
            print("Using DS18B20 sensor.")
            return
        except Exception as e4:
            print(f"DS18B20 not found: {e4}")

        # Fallback to internal sensor
        self.temp_sensor = InternalTempSensor()
        print("Using internal temperature sensor.")

    def read_temperature(self):
        result = {
            "temperature_f": None,
            "humidity": None,
            "pressure_inhg": None,
            "temp_sensor_type": "UNKNOWN",
        }

        try:
            if isinstance(self.temp_sensor, BME280Sensor):
                temperature_f, humidity, pressure_inhg = self.temp_sensor.read_values()
                result["temperature_f"] = temperature_f
                result["humidity"] = humidity
                result["pressure_inhg"] = pressure_inhg
                result["temp_sensor_type"] = "BME280"
            elif isinstance(self.temp_sensor, SHT31DSensor):
                temperature_f, humidity = self.temp_sensor.read_values()
                result["temperature_f"] = temperature_f
                result["humidity"] = humidity
                result["temp_sensor_type"] = "SHT31D"
            elif isinstance(self.temp_sensor, TMP117Sensor):
                temperature_f = self.temp_sensor.read_values()
                result["temperature_f"] = temperature_f
                result["temp_sensor_type"] = "TMP117"
            elif isinstance(self.temp_sensor, DS18B20Sensor):
                temperature_f = self.temp_sensor.read_values()
                result["temperature_f"] = temperature_f
                result["temp_sensor_type"] = "DS18B20"
            elif isinstance(self.temp_sensor, InternalTempSensor):
                temperature_f = self.temp_sensor.read_values()
                result["temperature_f"] = temperature_f
                result["temp_sensor_type"] = "INTERNAL"
            else:
                print("Unknown temperature sensor type")

            # Add Celsius temperature for fan controller
            if result["temperature_f"] is not None:
                # Convert Fahrenheit to Celsius: (F - 32) × 5/9 = C
                result["temperature_c"] = (result["temperature_f"] - 32) * 5 / 9

            return result
        except Exception as e:
            print(f"Error reading temperature sensor: {e}")
            return result

    def read_motion(self):
        try:
            current_motion_state = self.motion_sensor.read()
            motion_detected = (
                current_motion_state == "HIGH" and self.previous_motion_state == "LOW"
            )
            self.previous_motion_state = current_motion_state

            return {"motion": current_motion_state, "motion_detected": motion_detected}
        except Exception as e:
            print(f"Error reading motion sensor: {e}")
            return {"motion": "UNKNOWN", "motion_detected": False}

    def read_switch(self):
        try:
            current_switch_state = self.switch_sensor.read()
            switch_changed = current_switch_state != self.previous_switch_state
            self.previous_switch_state = current_switch_state

            return {"switch": current_switch_state, "switch_changed": switch_changed}
        except Exception as e:
            print(f"Error reading switch sensor: {e}")
            return {"switch": "UNKNOWN", "switch_changed": False}
