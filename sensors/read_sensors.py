# read_sensors.py

from sensors.bme280_sensor import BME280Sensor
from sensors.sht31d_sensor import SHT31DSensor
from sensors.internal_temp_sensor import InternalTempSensor

def get_all_sensor_readings(temp_sensor, motion_sensor, switch_sensor):
    readings = {}
    if isinstance(temp_sensor, BME280Sensor):
        temperature_f, humidity, pressure_inhg = temp_sensor.read_values()
    elif isinstance(temp_sensor, SHT31DSensor):
        temperature_f, humidity = temp_sensor.read_values()
        pressure_inhg = None
    elif isinstance(temp_sensor, InternalTempSensor):
        temperature_f = temp_sensor.read_values()
        humidity = None
        pressure_inhg = None
    else:
        temperature_f = humidity = pressure_inhg = None

    readings.update({
        "temperature_f": temperature_f,
        "humidity": humidity,
        "pressure_inhg": pressure_inhg,
        "motion": motion_sensor.read(),
        "switch": switch_sensor.read(),
    })

    return readings
