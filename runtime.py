# runtime.py

import time
import gc

from utils.payload_formatter import PayloadFormatter
from connections.mqtt_manager import MQTTManager
from connections.api_manager import APIManager
from utils.logger import Logger
from utils.fan_pwm_controller import FanPWMController
from utils.fan_step_controller import FanStepController


def run_loop(state):
    """
    Main application loop: handles sensor reads, config reloads, publishing, and cleanup.
    """
    logger: Logger = state["logger"]
    logger.log("Starting main loop...")
    time.sleep_ms(1000)

    while True:
        try:
            gc.collect()
            now = time.ticks_ms()

            # Update uptime tracker and LED indicator
            state["uptime"].update()
            state["led"].update()

            # Possibly reload configuration
            _maybe_reload_config(state, now)

            # Read all sensors and update state['readings']
            _read_sensors(state, now)

            # Publish to MQTT and/or API if needed
            _publish(state, now)

            # Pace the loop based on shortest period
            min_period = min(
                state["motion_period"],
                state["switch_period"],
                state["temp_period"],
                500,
            )
            time.sleep_ms(max(100, min_period // 4))

        except KeyboardInterrupt:
            logger.log("Ctrl+C detected, exiting main loop...")
            break

        except Exception as e:
            logger.log(f"Error in main loop: {e}")
            time.sleep_ms(1000)

    _cleanup(state)


def _maybe_reload_config(state, now):
    logger = state["logger"]
    if time.ticks_diff(now, state["last_cfg_check"]) < state["cfg_period"]:
        return

    new_cfg = state["config_loader"].check_config()
    if not new_cfg or new_cfg is state["config"]:
        state["last_cfg_check"] = now
        return

    logger.log("New config detected, reinitializing…")
    state["config"] = new_cfg

    if state.get("mqtt"):
        state["mqtt"].disconnect()
        state["mqtt"] = None

    state.update(
        {
            "device_enabled": new_cfg.get("enabled", state["device_enabled"]),
            "mqtt_cfg": new_cfg.get("mqtt_config", state["mqtt_cfg"]),
            "mqtt_enabled": new_cfg.get("mqtt_config", {}).get(
                "enabled", state["mqtt_enabled"]
            ),
            "api_cfg": new_cfg.get("api_config", state["api_cfg"]),
            "api_enabled": new_cfg.get("api_config", {}).get(
                "enabled", state["api_enabled"]
            ),
            "heartbeat_period": new_cfg.get(
                "heartbeat_publish_period", state["heartbeat_period"]
            ),
            "mqtt_reconnect_delay": new_cfg.get(
                "mqtt_reconnect_delay", state["mqtt_reconnect_delay"]
            ),
            "motion_cooldown": new_cfg.get(
                "motion_cooldown_wait_period", state["motion_cooldown"]
            ),
            "motion_period": new_cfg.get("motion_check_period", state["motion_period"]),
            "switch_period": new_cfg.get("switch_check_period", state["switch_period"]),
            "temp_period": new_cfg.get(
                "temperature_check_period", state["temp_period"]
            ),
            "cfg_period": new_cfg.get("check_config_file_period", state["cfg_period"]),
        }
    )

    state["mqtt"] = MQTTManager(state["device_id"], state["mqtt_cfg"])
    if state["api_enabled"]:
        try:
            state["api"] = APIManager(state["device_id"], state["api_cfg"])
        except ValueError as e:
            logger.log(f"API init failed: {e}")
            state["api"], state["api_enabled"] = None, False

    logger.set_device_info(state["device_id"], new_cfg.get("name", state["device_id"]))
    logger.set_mqtt_manager(state["mqtt"])
    logger.configure_remote_logging(new_cfg)

    if state.get("fan_pwm") is None:
        logger.log("Initializing fan PWM controller…")
        state["fan_pwm"] = FanPWMController(new_cfg)
    else:
        logger.log("Reconfiguring fan PWM controller…")
        state["fan_pwm"].configure(new_cfg)

    if state.get("fan_step") is None:
        logger.log("Initializing fan step controller…")
        state["fan_step"] = FanStepController(new_cfg)
    else:
        logger.log("Reconfiguring fan step controller…")
        state["fan_step"].configure(new_cfg)

    state["last_publish"] = now - state["heartbeat_period"] + 2000
    state["last_cfg_check"] = now


def _read_sensors(state, now):
    readings = state["readings"]

    # Motion sensor
    if time.ticks_diff(now, state["last_motion_check"]) >= state["motion_period"]:
        if state["device_enabled"]:
            m = state["sensors"].read_motion()
            if m:
                readings["motion"] = m["motion"]
                state["motion_event"] = m["motion_detected"]
        state["last_motion_check"] = now

    # Switch sensor
    if time.ticks_diff(now, state["last_switch_check"]) >= state["switch_period"]:
        if state["device_enabled"]:
            s = state["sensors"].read_switch()
            if s:
                readings["switch"] = s["switch"]
                state["switch_event"] = s["switch_changed"]
        state["last_switch_check"] = now

    # Temperature sensor (and fan + OLED updates)
    if time.ticks_diff(now, state["last_temp_check"]) >= state["temp_period"]:
        if state["device_enabled"]:
            t = state["sensors"].read_temperature()
            if t:
                readings.update(t)
                # PWM fan
                if state.get("fan_pwm") and t.get("temperature_c") is not None:
                    readings["fan_pwm_duty"] = state["fan_pwm"].update(
                        t["temperature_c"]
                    )
                # Step fan
                if state.get("fan_step") and t.get("temperature_c") is not None:
                    readings["fan_step_active_fans"] = state["fan_step"].update(
                        t["temperature_c"]
                    )
                # OLED display
                if state["oled"].is_initialized():
                    tf = t["temperature_f"]
                    info = ""
                    if state["fan_pwm"] and state["fan_pwm"].enabled:
                        info = f" Fan:{readings['fan_pwm_duty']}%"
                    elif state["fan_step"] and state["fan_step"].enabled:
                        info = f" Fans:{readings['fan_step_active_fans']}"
                    state["oled"].bigline1(f"T:{tf:.1f}F{info}")
                    state["oled"].bigline2(f"T:{(tf-32)*5/9:.1f}C")
        state["last_temp_check"] = now


def _publish(state, now):
    logger = state["logger"]
    readings = state["readings"]

    # Inject new data elements
    readings["wifi_rssi"] = state["wifi"].get_rssi()
    readings["uptime_seconds"] = state["uptime"].get_uptime_seconds()
    readings["fan_pwm"] = readings.get("fan_pwm_duty", 0)
    readings["fans_active_level"] = readings.get("fan_step_active_fans", 0)

    # Determine triggers
    since_pub = time.ticks_diff(now, state["last_publish"])
    since_motion = time.ticks_diff(now, state["last_motion_pub"])
    allow_motion = since_motion >= state["motion_cooldown"]

    trig_motion = state.get("motion_event", False) and allow_motion
    trig_switch = state.get("switch_event", False)
    trig_heart = since_pub >= state["heartbeat_period"]

    if not state["device_enabled"] or not (trig_motion or trig_switch or trig_heart):
        return

    # Choose event type
    event_type = "heartbeat"
    if trig_motion:
        event_type = "motion"
    elif trig_switch:
        event_type = "switch"

    # Add formatted uptime string
    readings["uptime"] = state["uptime"].get_uptime_string()

    # Format and log payload
    payload = PayloadFormatter.mqtt_payload(state["device_id"], readings, event_type)
    logger.log(f"Payload: {payload}")

    # MQTT publish
    if state["mqtt_enabled"] and state.get("mqtt"):
        state["mqtt"].publish(payload)

    # API publish
    if state["api_enabled"] and state.get("api"):
        api_payload = PayloadFormatter.api_payload(
            state["device_id"], readings, event_type
        )
        state["api"].publish(api_payload)

    # Update timestamps
    state["last_publish"] = now
    if trig_motion:
        state["last_motion_pub"] = now


def _cleanup(state):
    # Deinitialize controllers and peripherals
    if state.get("fan_pwm"):
        state["fan_pwm"].deinit()
    if state.get("fan_step"):
        state["fan_step"].deinit()
    if state["oled"].is_initialized():
        state["oled"].deinit()
    state["led"].stop()
    if state.get("api"):
        state["api"].deinit()
