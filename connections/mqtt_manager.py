# connections/mqtt_manager.py

import time
import json
import gc
from lib.umqtt.simple import MQTTClient, connect_mqtt, MQTTException
from utils.logger import Logger

try:
    from ucollections import OrderedDict
except ImportError:
    try:
        from collections import OrderedDict
    except ImportError:
        OrderedDict = dict
        print("Warning: OrderedDict not found.")


class MQTTManager:
    def __init__(self, client_id, mqtt_config):
        # Validate required configuration
        required_keys = ["broker", "port", "base_topic", "reconnect_delay"]
        missing = [key for key in required_keys if key not in mqtt_config]
        if missing:
            raise ValueError(
                f"Missing required MQTT configuration: {', '.join(missing)}"
            )

        self.client_id = client_id
        self.config = mqtt_config
        self.client = None
        self.last_attempt = 0
        self.reconnect_delay = mqtt_config["reconnect_delay"]
        self.base_topic = mqtt_config["base_topic"]
        self.full_topic = f"{self.base_topic}/{self.client_id}"

        # Get the logger instance
        self.logger = Logger.get_instance()
        self.logger.log(
            f"MQTT Manager initialized for client '{self.client_id}'. Topic: '{self.full_topic}'"
        )

    # ---------------------------------------------------------------------
    # Connection helpers
    # ---------------------------------------------------------------------

    def connect(self):
        """Attempts to connect to MQTT broker"""
        current_time = time.time()
        if current_time - self.last_attempt < self.reconnect_delay:
            return False  # Still in cooldown

        self.logger.log("MQTT connecting...")
        self.last_attempt = current_time

        if self.client is not None:  # Disconnect previous if exists
            try:
                self.client.disconnect()
            except Exception as e:
                self.logger.log(f"Error disconnecting previous client: {e}")
        self.client = None

        gc.collect()

        try:
            # Optional parameters
            user = self.config.get("user")
            password = self.config.get("password")
            ssl = self.config.get("ssl", False)
            ssl_params = self.config.get("ssl_params", {})

            self.client = connect_mqtt(
                client_id=self.client_id,
                broker=self.config["broker"],
                port=self.config["port"],
                user=user,
                password=password,
                keepalive=60,
                ssl=ssl,
                ssl_params=ssl_params,
            )
        except OSError as e:
            self.logger.log(f"MQTT DNS or Network Error: {e}")
            self.client = None
            raise
        except Exception as e:
            self.logger.log(f"Unexpected Error during MQTT connect: {e}")
            self.client = None
            raise

        if self.client:
            self.logger.log("MQTT Connected Successfully!")
            return True
        else:
            self.logger.log("MQTT Connection Failed")
            return False

    def is_connected(self):
        return self.client is not None

    def ensure_connected(self):
        if not self.is_connected():
            return self.connect()
        return True

    # ---------------------------------------------------------------------
    # Payload helpers
    # ---------------------------------------------------------------------

    def format_payload(self, readings_dict, event_type):
        """Formats sensor readings plus extras into a JSON payload"""
        if not event_type:
            raise ValueError("Event type must be specified")

        message = OrderedDict()
        message["event_type"] = event_type
        message["device_id"] = self.client_id

        # Extract sensor values
        temp = readings_dict.get("temperature_f")
        humidity = readings_dict.get("humidity")
        pressure = readings_dict.get("pressure_inhg")
        temp_sensor_type = readings_dict.get("temp_sensor_type")
        motion = readings_dict.get("motion")
        switch = readings_dict.get("switch")

        # Temperature
        if temp is not None:
            try:
                message["temperature"] = round(float(temp), 1)
            except Exception as e:
                self.logger.log(f"Error converting temperature: {e}")
                message["temperature"] = None
        else:
            message["temperature"] = None

        # Humidity
        if humidity is not None:
            try:
                message["humidity"] = round(float(humidity), 1)
            except Exception as e:
                self.logger.log(f"Error converting humidity: {e}")
                message["humidity"] = None
        else:
            message["humidity"] = None

        # Pressure
        if pressure is not None:
            try:
                message["pressure"] = round(float(pressure), 2)
            except Exception as e:
                self.logger.log(f"Error converting pressure: {e}")
                message["pressure"] = None
        else:
            message["pressure"] = None

        # Strings / enums
        message["temp_sensor_type"] = (
            str(temp_sensor_type) if temp_sensor_type is not None else None
        )
        message["motion"] = str(motion) if motion is not None else None
        message["switch"] = str(switch) if switch is not None else None

        # Timestamp in UTC (ISO 8601)
        try:
            t = time.localtime()
            message["timestamp"] = (
                f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"
            )
        except Exception as e:
            self.logger.log(f"Error generating timestamp: {e}")
            raise

        # Extras supplied by caller (e.g., firmware version, uptime seconds)
        message["version"] = readings_dict.get("version")
        message["uptime"] = readings_dict.get("uptime")

        try:
            return json.dumps(message)
        except Exception as e:
            self.logger.log(f"Error creating JSON: {e}")
            raise

    # ---------------------------------------------------------------------
    # Publishing
    # ---------------------------------------------------------------------

    def publish(self, readings_dict, event_type):
        """Formats and publishes sensor readings with an event type"""
        if not self.is_connected():
            self.logger.log("MQTT Publish - connecting first...")
            if not self.connect():
                self.logger.log("MQTT connection failed")
                return False

        json_payload = self.format_payload(readings_dict, event_type)

        try:
            self.logger.log(
                f"Publishing ({event_type}) to {self.full_topic}: {json_payload}"
            )
            self.client.publish(self.full_topic, json_payload)
            self.logger.log("MQTT publish successful.")
            return True
        except (OSError, MQTTException) as e:
            self.logger.log(f"MQTT publish Error: {e}")
            self.client = None
            raise
        except Exception as e:
            self.logger.log(f"MQTT unexpected error during publish: {e}")
            self.client = None
            raise

    # ---------------------------------------------------------------------

    def disconnect(self):
        if self.client:
            try:
                self.client.disconnect()
                self.logger.log("MQTT disconnected.")
            except Exception as e:
                self.logger.log(f"Error during MQTT disconnect: {e}")
                raise
        self.client = None
