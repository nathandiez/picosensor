# connections/mqtt_manager.py

import time
import json
import gc
from lib.umqtt.simple import MQTTClient, connect_mqtt, MQTTException

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
        self.client_id = client_id
        self.config = mqtt_config # Store the whole MQTT_CONFIG dict
        self.client = None
        self.last_attempt = 0
        self.reconnect_delay = self.config.get("MQTT_RECONNECT_DELAY_SECONDS", 10)
        self.base_topic = self.config.get("BASE_TOPIC", "home/sensors")
        self.full_topic = f"{self.base_topic}/{self.client_id}"
        print(f"MQTT Manager initialized for client '{self.client_id}'. Topic: '{self.full_topic}'")

    def connect(self):
        """Attempts to connect to MQTT broker"""
        current_time = time.time()
        if current_time - self.last_attempt < self.reconnect_delay:
            return False # Still in cooldown

        print("Attempting MQTT connection...")
        self.last_attempt = current_time

        if self.client is not None: # Disconnect previous if exists
            try: self.client.disconnect()
            except Exception: pass
        self.client = None

        gc.collect()
        print(f"MQTT connection Mem Free: {gc.mem_free()} bytes")

        try:
            self.client = connect_mqtt(
                client_id=self.client_id,
                broker=self.config["BROKER"],
                port=self.config["PORT"],
                user=self.config.get("USER"),
                password=self.config.get("PASSWORD"),
                keepalive=60,
                ssl=self.config.get("SSL", False),
                ssl_params=self.config.get("SSL_PARAMS", {})
            )
        except OSError as e:
            print(f"MQTT DNS or Network Error: {e}")
            self.client = None
        except Exception as e:
            print(f"Unexpected Error during MQTT connect: {e}")
            self.client = None

        if self.client:
            print("MQTT Connected Successfully!")
            return True
        else:
            print("MQTT Connection Attempt Failed.")
            return False

    def is_connected(self):
        # Basic check. A ping would be more robust but adds complexity.
        return self.client is not None

    def ensure_connected(self):
        if not self.is_connected():
            return self.connect()
        return True

    def publish(self, readings_dict, event_type="unknown"):
        """Formats and publishes sensor readings with an event type"""
        if not self.is_connected():
            print("MQTT not connected, cannot publish.")
            return False

        message = OrderedDict()
        message["event_type"] = event_type
        message["device_id"] = self.client_id

        temp = readings_dict.get("temperature_f")
        humidity = readings_dict.get("humidity")
        pressure = readings_dict.get("pressure_inhg")
        motion = readings_dict.get("motion", "UNKNOWN")
        switch = readings_dict.get("switch", "UNKNOWN")

        message["temperature"] = round(temp, 1) if temp is not None else None
        message["humidity"] = round(humidity, 1) if humidity is not None else None
        message["pressure"] = round(pressure, 2) if pressure is not None else None
        message["motion"] = motion
        message["switch"] = switch

        # Add timestamp
        try:
            t = time.localtime()
            message["timestamp"] = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                t[0], t[1], t[2], t[3], t[4], t[5]
            )
        except Exception as e:
            print(f"Error getting timestamp: {e}")
            message["timestamp"] = "1970-01-01 00:00:00"

        try:
            json_payload = json.dumps(message)
        except Exception as e:
            print(f"Error creating JSON: {e}")
            return False

        # Publish
        try:
            print(f"Publishing ({event_type}) to {self.full_topic}: {json_payload}")
            self.client.publish(self.full_topic, json_payload)
            print("Message Sent Successfully.")
            return True
        except (OSError, MQTTException) as e:
            print(f"MQTT Publish Error (Network/Broker): {e}. Assuming disconnect.")
            self.client = None
            return False
        except Exception as e:
            print(f"Unexpected error during publish: {e}")
            self.client = None
            return False



    def disconnect(self):
        # (disconnect method remains the same)
        if self.client:
            try:
                self.client.disconnect()
                print("MQTT disconnected.")
            except Exception as e:
                print(f"Ignoring error during MQTT disconnect: {e}")
        self.client = None