# app.py

import time
import machine
import gc
from config.settings import (
    WIFI_CONFIG, MQTT_CONFIG, TEMP_SENSOR_PINS,
    MOTION_SENSOR_PIN, SWITCH_SENSOR_PIN,
    MAIN_LOOP_DELAY,
    MQTT_RECONNECT_DELAY,
    MOTION_WAIT_PERIOD,
    MOTION_CHECK_INTERVAL,
    SWITCH_CHECK_INTERVAL,
    TEMPERATURE_CHECK_INTERVAL
)
from connections.wifi_manager import WiFiManager
from connections.mqtt_manager import MQTTManager
from sensors.bme280_sensor import BME280Sensor
from sensors.sht31d_sensor import SHT31DSensor
from sensors.internal_temp_sensor import InternalTempSensor
from sensors.motion_sensor import MotionSensor
from sensors.switch_sensor import SwitchSensor
from sensors.read_sensors import get_all_sensor_readings
from utils.device_id import get_device_id
from utils.led_indicator import LEDIndicator


# --- Main Execution Logic ---
def run_application():
    device_id = get_device_id()
    print(f"Device ID: {device_id}")

    # Initialize LED indicator
    led_indicator = LEDIndicator()
    
    try:
        print("Initializing WiFi...")
        wifi = WiFiManager(WIFI_CONFIG["SSID"], WIFI_CONFIG["PASSWORD"])
        if not wifi.connect():
            raise RuntimeError("Initial WiFi connection failed")

        mqtt_enabled = MQTT_CONFIG.get("ENABLED", False)
        mqtt = None
        mqtt_reconnect_delay = MQTT_CONFIG.get("MQTT_RECONNECT_DELAY", 10000)

        if mqtt_enabled:
            mqtt = MQTTManager(device_id, MQTT_CONFIG)
        else:
            print("MQTT is disabled in settings.")

        print("Initializing Sensors...")
        try:
            try:
                temp_sensor = BME280Sensor(TEMP_SENSOR_PINS)
                print("Using BME280 sensor.")
            except Exception as e1:
                print(f"BME280 not found: {e1}")
                try:
                    temp_sensor = SHT31DSensor(TEMP_SENSOR_PINS)
                    print("Using SHT31D sensor.")
                except Exception as e2:
                    print(f"SHT31D not found: {e2}")
                    temp_sensor = InternalTempSensor()
                    print("Using internal temperature sensor.")

            motion_sensor = MotionSensor(MOTION_SENSOR_PIN)
            switch_sensor = SwitchSensor(SWITCH_SENSOR_PIN)
            previous_motion_state = motion_sensor.read()
            previous_switch_state = switch_sensor.read()

            print(f"Initial Motion: {previous_motion_state}, Initial Switch: {previous_switch_state}")

        except Exception as e:
            raise RuntimeError(f"Sensor initialization failed: {e}")

        # Start LED blinking after successful initialization
        led_indicator.start(1000)  # Blink once per second
            
        print("Starting main loop...")
        last_publish_time = time.ticks_ms() - MAIN_LOOP_DELAY
        last_motion_publish_time = 0
        last_motion_check_time = 0
        last_switch_check_time = 0
        last_temperature_check_time = 0
        
        # Store most recent reading values
        current_readings = {
            "temperature_f": None,
            "humidity": None,
            "pressure_inhg": None,
            "motion": "UNKNOWN",
            "switch": "UNKNOWN"
        }
        
        while True:
            gc.collect()
            current_time = time.ticks_ms()
            
            # Update LED indicator (non-blocking)
            led_indicator.update()

            if not wifi.ensure_connected():
                print(f"WiFi disconnected, retrying in {mqtt_reconnect_delay//1000}s...")
                if mqtt: mqtt.client = None
                time.sleep_ms(mqtt_reconnect_delay)
                continue

            if mqtt_enabled and (mqtt is None or not mqtt.ensure_connected()):
                print(f"MQTT disconnected, retrying in {mqtt_reconnect_delay//1000}s...")
                time.sleep_ms(mqtt_reconnect_delay)
                continue

            check_motion = time.ticks_diff(current_time, last_motion_check_time) >= MOTION_CHECK_INTERVAL
            check_switch = time.ticks_diff(current_time, last_switch_check_time) >= SWITCH_CHECK_INTERVAL
            check_temperature = time.ticks_diff(current_time, last_temperature_check_time) >= TEMPERATURE_CHECK_INTERVAL
            
            motion_detected_now = False
            switch_changed = False
            
            # Check motion sensor
            if check_motion:
                try:
                    current_motion_state = motion_sensor.read()
                    motion_detected_now = current_motion_state == "HIGH" and previous_motion_state == "LOW"
                    previous_motion_state = current_motion_state
                    current_readings["motion"] = current_motion_state
                    last_motion_check_time = current_time
                except Exception as e:
                    print(f"Error reading motion sensor: {e}")
            
            # Check switch sensor
            if check_switch:
                try:
                    current_switch_state = switch_sensor.read()
                    switch_changed = current_switch_state != previous_switch_state
                    previous_switch_state = current_switch_state
                    current_readings["switch"] = current_switch_state
                    last_switch_check_time = current_time
                except Exception as e:
                    print(f"Error reading switch sensor: {e}")
            
            # Check temperature sensor
            if check_temperature:
                try:
                    if isinstance(temp_sensor, BME280Sensor):
                        temperature_f, humidity, pressure_inhg = temp_sensor.read_values()
                        current_readings["temperature_f"] = temperature_f
                        current_readings["humidity"] = humidity
                        current_readings["pressure_inhg"] = pressure_inhg
                    elif isinstance(temp_sensor, SHT31DSensor):
                        temperature_f, humidity = temp_sensor.read_values()
                        current_readings["temperature_f"] = temperature_f
                        current_readings["humidity"] = humidity
                        current_readings["pressure_inhg"] = None
                    elif isinstance(temp_sensor, InternalTempSensor):
                        temperature_f = temp_sensor.read_values()
                        current_readings["temperature_f"] = temperature_f
                        current_readings["humidity"] = None
                        current_readings["pressure_inhg"] = None
                    last_temperature_check_time = current_time
                except Exception as e:
                    print(f"Error reading temperature sensor: {e}")
                    
            time_since_last_publish = time.ticks_diff(current_time, last_publish_time)
            time_since_last_motion_publish = time.ticks_diff(current_time, last_motion_publish_time)

            allow_motion_publish = (time_since_last_motion_publish >= MOTION_WAIT_PERIOD)
            triggered_by_motion = motion_detected_now and allow_motion_publish
            triggered_by_switch = switch_changed
            triggered_by_timer = (time_since_last_publish >= MAIN_LOOP_DELAY)

            should_publish = triggered_by_motion or triggered_by_switch or triggered_by_timer

            if mqtt_enabled and mqtt and should_publish:
                event_type = "unknown"
                if triggered_by_motion:
                    event_type = "motion"
                elif triggered_by_switch:
                    event_type = "switch"
                elif triggered_by_timer:
                    event_type = "heartbeat"

                print(f"Publish trigger: {event_type}")

                if mqtt.publish(current_readings, event_type):
                    last_publish_time = current_time
                    if triggered_by_motion:
                        last_motion_publish_time = current_time

            elif motion_detected_now and not allow_motion_publish:
                remaining_cooldown = (MOTION_WAIT_PERIOD - time_since_last_motion_publish) // 1000
                print(f"Motion detected but in cooldown ({remaining_cooldown:.1f}s left)")

            # Sleep for smallest interval to ensure we don't miss any readings
            min_interval = min(MOTION_CHECK_INTERVAL, SWITCH_CHECK_INTERVAL)
            time.sleep_ms(min_interval)
    
    finally:
        # Ensure LED is turned off when exiting
        led_indicator.stop()

if __name__ == "__main__":
    try:
        run_application()
    except KeyboardInterrupt:
        print("Ctrl+C pressed, exiting.")
    except Exception as e:
        print(f"FATAL error: {e}")
        print("Rebooting in 30 seconds...")
        time.sleep_ms(30000)
        machine.reset()