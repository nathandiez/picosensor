# app.py
import time
import machine
import gc
import json

from config.config_loader import ConfigLoader
from connections.wifi_manager import WiFiManager
from connections.mqtt_manager import MQTTManager
from sensors.sensor_manager import SensorManager
from displays.OLED1306Manager import OLED1306Display
from utils.device_id import get_device_id
from utils.led_indicator import LEDIndicator
from utils.logger import Logger
from utils.fan_controller import FanController

# --- Main Execution Logic ---


def run_application():
    print("\n################ Starting up ################")

    # Create basic logger immediately (local only initially)
    logger = Logger.get_instance()
    logger.log("Boot: Logger created")

    # Get device ID (needed for both config and logger)
    device_id = get_device_id()
    logger.log(f"Device ID: {device_id}")

    # Visual indicator for startup
    led_indicator = LEDIndicator()
    led_indicator.start(500)  # Fast blink during init

    # Initialize WiFi early - don't wait for config
    # This gets network connectivity established ASAP
    logger.log("Connecting WiFi...")
    wifi = WiFiManager()
    if not wifi.connect():
        logger.log("WiFi failed")
        raise RuntimeError("WiFi init failed")
    logger.log("WiFi connected")

    # Now load config after WiFi is ready
    config_loader = ConfigLoader(device_id)
    config = config_loader.load_config()

    if config is None:
        logger.log("FATAL: failed to load configuration, restarting...")
        time.sleep_ms(5000)
        machine.reset()

    # Set up device info and remote logging as early as possible
    # This happens right after we have both WiFi and config
    logger.set_device_info(device_id, config.get("name", device_id))
    logger.configure_remote_logging(config)
    logger.log("--- Remote logging initialized ---")

    # Now proceed with the rest of the initialization
    # Extract config settings
    oled_cfg = config["oled_config"]
    temp_pins = config["temp_sensor_pins"]
    motion_pin = config["motion_sensor_pin"]
    switch_pin = config["switch_sensor_pin"]
    onewire_data_pin = config["onewire_data_pin"]

    # Create OLED and attach to logger
    oled = OLED1306Display(oled_cfg)
    logger.set_display(oled)

    if oled.is_initialized():
        oled.bigline1("Initializing...")
    else:
        logger.log("OLED failed to initialize")

    # Continue with sensor initialization and main loop...

    try:
        logger.log("Initializing Sensors...")
        sensor_manager = SensorManager(
            temp_pins,
            motion_pin,
            switch_pin,
            onewire_data_pin,
        )
        if not sensor_manager.initialize_sensors():
            raise RuntimeError("Sensor initialization failed")

        logger.log("Starting main loop...")
        # Set initial check times
        last_publish_time = 0
        last_motion_publish_time = 0
        last_motion_check_time = 0
        last_switch_check_time = 0
        last_temperature_check_time = 0
        last_check_config_file_time = time.ticks_ms() - (
            24 * 60 * 60 * 1000
        )  # ~1 day ago in ms

        # Initialize default values (will be overridden by config)
        device_enabled = False
        mqtt_enabled = False
        heartbeat_publish_period = 60000  # Default: 1 minute
        mqtt_reconnect_delay = 10000  # Default: 10 seconds
        motion_cooldown_period = 30000  # Default: 30 seconds
        motion_check_period = 500  # Default: 0.5 seconds
        switch_check_period = 500  # Default: 0.5 seconds
        temperature_check_period = 30000  # Default: 30 seconds
        check_config_file_period = 60000  # Default: 1 minute

        current_readings = {
            "temperature_f": None,
            "humidity": None,
            "pressure_inhg": None,
            "motion": "UNKNOWN",
            "switch": "UNKNOWN",
            "fan_duty": 0,  # Added fan_duty to readings
        }
        logger.log("Enter Loop...")
        time.sleep_ms(1000)

        # Initialize mqtt and fan_controller variables
        mqtt = None
        fan_controller = None

        while True:
            try:
                gc.collect()
                current_time = time.ticks_ms()

                led_indicator.update()  # Update LED state

                # Always check for config updates first
                check_config_file = (
                    time.ticks_diff(current_time, last_check_config_file_time)
                    >= check_config_file_period
                )

                if check_config_file:
                    new_config = config_loader.check_config()
                    if new_config is not None and new_config is not config:
                        logger.log("New config file!")
                        config = new_config
                        if mqtt is not None:
                            mqtt.disconnect()
                            mqtt = None  # Reset MQTT connection
                        logger.log("re-initializing all configs...")

                        # Update using snake_case naming convention
                        device_enabled = config.get("enabled", 0)
                        mqtt_config = config.get("mqtt_config", {})
                        mqtt_enabled = mqtt_config.get("enabled", False)

                        # Get configuration using snake_case
                        heartbeat_publish_period = config.get(
                            "heartbeat_publish_period", heartbeat_publish_period
                        )
                        mqtt_reconnect_delay = config.get(
                            "mqtt_reconnect_delay", mqtt_reconnect_delay
                        )
                        motion_cooldown_period = config.get(
                            "motion_cooldown_wait_period", motion_cooldown_period
                        )
                        motion_check_period = config.get(
                            "motion_check_period", motion_check_period
                        )
                        switch_check_period = config.get(
                            "switch_check_period", switch_check_period
                        )
                        temperature_check_period = config.get(
                            "temperature_check_period", temperature_check_period
                        )
                        check_config_file_period = config.get(
                            "check_config_file_period", check_config_file_period
                        )

                        logger.log(
                            f"Device '{config.get('name', device_id)}' enable flag = {device_enabled}"
                        )
                        logger.log(f"MQTT enabled: {mqtt_enabled}")

                        # Initialize MQTT for events
                        mqtt = MQTTManager(device_id, mqtt_config)

                        # Configure logger with device info
                        logger.set_device_info(device_id, config.get("name", device_id))

                        # Set MQTT manager on logger
                        logger.set_mqtt_manager(mqtt)

                        # Configure remote logging (both HTTP and MQTT)
                        logger.configure_remote_logging(config)

                        # Initialize or reconfigure fan controller
                        if fan_controller is None:
                            logger.log("Initializing fan controller...")
                            fan_controller = FanController(config)
                        else:
                            logger.log("Reconfiguring fan controller...")
                            fan_controller.configure(config)

                        last_publish_time = (
                            time.ticks_ms() - heartbeat_publish_period + 2000
                        )  # First publish in 2 seconds

                    last_check_config_file_time = current_time

                check_motion = (
                    time.ticks_diff(current_time, last_motion_check_time)
                    >= motion_check_period
                )
                check_switch = (
                    time.ticks_diff(current_time, last_switch_check_time)
                    >= switch_check_period
                )
                check_temperature = (
                    time.ticks_diff(current_time, last_temperature_check_time)
                    >= temperature_check_period
                )

                motion_detected_now = False
                switch_changed = False

                if check_motion:
                    # logger.log("Checking Motion...")
                    motion_data = None
                    if device_enabled:
                        motion_data = sensor_manager.read_motion()
                        if motion_data is not None:  # Explicit check
                            current_readings["motion"] = motion_data["motion"]
                            motion_detected_now = motion_data["motion_detected"]
                    last_motion_check_time = current_time

                if check_switch:
                    switch_data = None
                    if device_enabled:
                        switch_data = sensor_manager.read_switch()
                        if switch_data is not None:  # Explicit check
                            current_readings["switch"] = switch_data["switch"]
                            switch_changed = switch_data["switch_changed"]
                    last_switch_check_time = current_time

                if check_temperature:
                    # logger.log("Reading temperature...")
                    temp_data = None
                    if device_enabled:
                        temp_data = sensor_manager.read_temperature()
                        if temp_data is not None:  # Explicit check
                            current_readings.update(temp_data)

                            # Update fan controller with current temperature
                            if (
                                fan_controller is not None
                                and "temperature_c" in temp_data
                            ):
                                fan_duty = fan_controller.update(
                                    temp_data["temperature_c"]
                                )
                                # Add fan duty to current readings for MQTT publishing
                                current_readings["fan_duty"] = fan_duty

                            # Display temperature on OLED headline
                            if oled.is_initialized():
                                temp_f = temp_data.get("temperature_f")
                                fan_info = ""
                                # if "fan_duty" in current_readings and current_readings["fan_duty"] > 0:
                                fan_info = f"  Fan:{current_readings['fan_duty']}%"
                                # logger.log(f"Fan duty: {current_readings['fan_duty']}%")
                                oled.bigline1(f"T:{temp_f:.1f} F{fan_info}")
                                oled.bigline2(f"T:{temp_f*5/9:.1f}C")
                    last_temperature_check_time = current_time

                # --- Publish Logic (using intervals/periods from config) ---
                time_since_last_publish = time.ticks_diff(
                    current_time, last_publish_time
                )
                time_since_last_motion_publish = time.ticks_diff(
                    current_time, last_motion_publish_time
                )

                allow_motion_publish = (
                    time_since_last_motion_publish >= motion_cooldown_period
                )
                triggered_by_motion = motion_detected_now and allow_motion_publish
                triggered_by_switch = switch_changed
                triggered_by_heartbeat = (
                    time_since_last_publish >= heartbeat_publish_period
                )

                should_publish = (
                    triggered_by_motion or triggered_by_switch or triggered_by_heartbeat
                )

                if should_publish and device_enabled:
                    event_type = "heartbeat"
                    if triggered_by_motion:
                        event_type = "motion"
                    elif triggered_by_switch:
                        event_type = "switch"

                    json_payload = mqtt.format_payload(current_readings, event_type)
                    logger.log(f"MQTT event: {event_type}: {json_payload}")

                    if mqtt_enabled and mqtt is not None:
                        if mqtt.publish(current_readings, event_type):
                            last_publish_time = current_time
                            if triggered_by_motion:
                                last_motion_publish_time = current_time
                        else:
                            logger.log("MQTT publish failed.")
                            # Still update timestamps to prevent immediate retries
                            last_publish_time = current_time
                            if triggered_by_motion:
                                last_motion_publish_time = current_time
                    else:
                        # MQTT disabled but still update timestamps
                        last_publish_time = current_time
                        if triggered_by_motion:
                            last_motion_publish_time = current_time

                elif motion_detected_now and not allow_motion_publish:
                    remaining_cooldown = (
                        max(
                            0, (motion_cooldown_period - time_since_last_motion_publish)
                        )
                        // 1000
                    )
                    # logger.log(f"Motion detected but in cooldown ({remaining_cooldown}s left)") # Reduce verbosity

                # --- Loop Delay ---
                min_period = min(
                    motion_check_period,
                    switch_check_period,
                    temperature_check_period,
                    500,
                )  # e.g., check at least twice per second
                # Sleep briefly but ensure responsiveness
                sleep_duration = max(100, min_period // 4)
                time.sleep_ms(sleep_duration)

            except KeyboardInterrupt:
                logger.log("Ctrl+C detected, exiting main loop...")
                break  # Exit the loop on Ctrl+C

            except Exception as e:
                # Handle loop-specific exceptions without exiting the function
                logger.log(f"Error in main loop: {e}")
                time.sleep_ms(1000)  # Short pause after an error

    except Exception as e:
        # Use str(e) for safety, check if led_indicator exists
        logger.log(f"FATAL error in run_application: {str(e)}")
        logger.log("Activating error LED pattern (fast blink)...")
        if led_indicator:  # Check if led_indicator was successfully initialized
            led_indicator.start(100)  # Fast flash
        logger.log("Rebooting in 30 seconds...")
        time.sleep(30)  # Use time.sleep() as time_ms isn't imported
        machine.reset()

    finally:
        # Clean up resources
        if "fan_controller" in locals() and fan_controller:
            fan_controller.deinit()
        # Ensure LED is turned off if loop exits normally (e.g., device disabled)
        if led_indicator:
            led_indicator.stop()
        logger.log("Application stopped.")


if __name__ == "__main__":
    try:
        run_application()
    except KeyboardInterrupt:
        print("Ctrl+C pressed, exiting.")
    except Exception as e:
        print(f"Critical bootstrap error: {e}")
        print("Rebooting in 30 seconds...")
        time.sleep(30)
        machine.reset()
