# connections/mqtt_manager.py
import time
from lib.umqtt.simple import connect_mqtt, MQTTException
from utils.logger import Logger


class MQTTManager:
    def __init__(self, client_id, mqtt_config):
        required = ["broker", "port", "base_topic", "reconnect_delay"]
        missing = [k for k in required if k not in mqtt_config]
        if missing:
            raise ValueError(f"Missing MQTT config: {', '.join(missing)}")

        self.client_id = client_id
        self.config = mqtt_config
        self.client = None
        self.last_attempt = 0
        self.reconnect_delay = mqtt_config["reconnect_delay"]
        self.topic = f"{mqtt_config['base_topic']}/{client_id}"
        self.logger = Logger.get_instance()
        self.logger.log(f"MQTT Manager init: topic={self.topic}")

    def connect(self):
        now = time.time()
        if now - self.last_attempt < self.reconnect_delay:
            return False
        self.last_attempt = now

        if self.client:
            try:
                self.client.disconnect()
            except:
                pass
            self.client = None

        self.logger.log("MQTT connecting...")
        try:
            self.client = connect_mqtt(
                client_id=self.client_id,
                broker=self.config["broker"],
                port=self.config["port"],
                user=self.config.get("user"),
                password=self.config.get("password"),
                keepalive=60,
                ssl=self.config.get("ssl", False),
                ssl_params=self.config.get("ssl_params", {}),
            )
        except Exception as e:
            self.logger.log(f"MQTT connect error: {e}")
            self.client = None
            return False

        self.logger.log("MQTT connected")
        return True

    def publish(self, json_payload):
        """Publish a pre-formatted JSON payload string"""
        if not self.client and not self.connect():
            self.logger.log("MQTT publish aborted: not connected")
            return False
        try:
            self.client.publish(self.topic, json_payload)
            self.logger.log("MQTT publish successful")
            return True
        except (OSError, MQTTException) as e:
            self.logger.log(f"MQTT publish error: {e}")
            self.client = None
            return False

    def disconnect(self):
        if self.client:
            try:
                self.client.disconnect()
                self.logger.log("MQTT disconnected")
            except Exception as e:
                self.logger.log(f"MQTT disconnect error: {e}")
        self.client = None
