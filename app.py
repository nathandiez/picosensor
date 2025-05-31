# app.py

import time
import machine
import json
import gc

from config.config_loader import ConfigLoader
from connections.wifi_manager import WiFiManager
from sensors.sensor_manager import SensorManager
from displays.OLED1306Manager import OLED1306Display
from utils.device_id import get_device_id
from utils.led_indicator import LEDIndicator
from utils.logger import Logger
from utils.uptime_tracker import UptimeTracker
from runtime import run_loop  # your existing runtime.py

version = "v1.053025"


def bootstrap():
    print("\n################ Starting up ################")

    # OLED
    oled = OLED1306Display()
    if oled.is_initialized():
        oled.bigline1("Initializing...")
        oled.bigline2(version)
    else:
        print("OLED failed to initialize")

    # Logger
    logger = Logger.get_instance()
    logger.set_display(oled)
    logger.log("Boot: Logger created")

    # Device ID
    device_id = get_device_id()
    logger.log(f"Device ID: {device_id}")

    # Uptime tracker
    uptime = UptimeTracker()
    logger.log("Uptime tracker initialized")

    # LED indicator
    led = LEDIndicator()
    led.start(500)

    # Wi-Fi
    logger.log("Connecting WiFi...")
    try:
        wifi = WiFiManager()
        if not wifi.connect():
            raise RuntimeError("returned False")
        logger.log("WiFi connected")
    except Exception as e:
        raise RuntimeError(f"WiFi init failed: {e}")

    # Config
    cfg_loader = ConfigLoader(device_id)
    try:
        config = cfg_loader.load_config()
        if config is None:
            raise RuntimeError("returned None")
    except Exception as e:
        raise RuntimeError(f"Config loading failed: {e}")

    # Remote logging
    logger.set_device_info(device_id, config.get("name", device_id))
    logger.configure_remote_logging(config)
    logger.log("--- Remote logging initialized ---")

    # Sensors
    logger.log("Initializing Sensors...")
    sensors = SensorManager(
        config["i2c_temp_sensor_pins"],
        config["motion_sensor_pin"],
        config["switch_sensor_pin"],
        config["onewire_ds18b20_pin"],
    )
    if not sensors.initialize_sensors():
        raise RuntimeError("Sensor initialization failed")

    # Build shared state
    state = {
        "oled": oled,
        "logger": logger,
        "device_id": device_id,
        "uptime": uptime,
        "led": led,
        "wifi": wifi,
        "config_loader": cfg_loader,
        "config": config,
        "sensors": sensors,
        "mqtt": None,
        "api": None,
        "fan_pwm": None,
        "fan_step": None,
        "last_publish": 0,
        "last_motion_pub": 0,
        "last_motion_check": 0,
        "last_switch_check": 0,
        "last_temp_check": 0,
        "last_cfg_check": time.ticks_ms() - (24 * 60 * 60 * 1000),
        "device_enabled": config.get("enabled", False),
        "mqtt_cfg": config.get("mqtt_config", {}),
        "mqtt_enabled": config.get("mqtt_config", {}).get("enabled", False),
        "api_cfg": config.get("api_config", {}),
        "api_enabled": config.get("api_config", {}).get("enabled", False),
        "heartbeat_period": config.get("heartbeat_publish_period", 60000),
        "mqtt_reconnect_delay": config.get("mqtt_reconnect_delay", 10000),
        "motion_cooldown": config.get("motion_cooldown_wait_period", 30000),
        "motion_period": config.get("motion_check_period", 500),
        "switch_period": config.get("switch_check_period", 500),
        "temp_period": config.get("temperature_check_period", 30000),
        "cfg_period": config.get("check_config_file_period", 60000),
        "readings": {
            "temperature_f": None,
            "humidity": None,
            "pressure_inhg": None,
            "motion": "UNKNOWN",
            "switch": "UNKNOWN",
            "fan_pwm_duty": 0,
            "fan_step_fans": 0,
            "version": version,
        },
    }

    return state


if __name__ == "__main__":
    try:
        state = bootstrap()
        run_loop(state)
    except KeyboardInterrupt:
        print("Ctrl+C pressed, exiting.")
    except Exception as e:
        print(f"Critical bootstrap error: {e}")
        print("Rebooting in 10 seconds...")
        time.sleep(10)
        machine.reset()