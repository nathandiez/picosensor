# utils/logger.py
import time
import json
import urequests


class Logger:
    # Singleton instance
    _instance = None

    def __init__(self, display_manager=None):
        # Set this instance as the singleton
        Logger._instance = self

        self.mqtt_manager = None
        self.display_manager = display_manager
        self.device_id = ""
        self.device_name = ""

        # Remote logging configuration
        self.mqtt_logging_enabled = False
        self.mqtt_base_topic = "pico-ulog"

        self.http_logging_enabled = False
        self.http_url = "http://uterm.local:5000/terminal"

        # Always show on serial
        print("Logger initialized")

    @classmethod
    def get_instance(cls):
        """Get the singleton instance, creating one if needed"""
        if cls._instance is None:
            cls._instance = Logger()
        return cls._instance

    def set_mqtt_manager(self, mqtt_manager):
        self.mqtt_manager = mqtt_manager
        print("Logger: MQTT Manager set")

    def set_device_info(self, device_id, device_name):
        self.device_id = device_id
        self.device_name = device_name
        print(f"Logger: Device info set to {self.device_id} ({self.device_name})")

    def configure_remote_logging(self, config):
        """Configure remote logging options based on configuration"""
        if not config:
            print("Logger: No config provided, remote logging disabled")
            self.mqtt_logging_enabled = False
            self.http_logging_enabled = False
            return

        # Get remote logger config if it exists
        remote_logger = config.get("remote_logger", {})

        # Configure MQTT logging
        mqtt_config = remote_logger.get("mqtt", {})
        self.mqtt_logging_enabled = mqtt_config.get("enabled", False)
        self.mqtt_base_topic = mqtt_config.get("base_topic", "az_iots3/ulog")
        print(
            f"Logger: MQTT logging {'enabled' if self.mqtt_logging_enabled else 'disabled'}"
        )

        # Configure HTTP logging
        http_config = remote_logger.get("http", {})
        self.http_logging_enabled = http_config.get("enabled", False)
        self.http_url = http_config.get("url", "http://uterm.local:5000/terminal")
        print(
            f"Logger: HTTP logging {'enabled' if self.http_logging_enabled else 'disabled'} to {self.http_url}"
        )

    def format_message(self, message):
        if not self.device_id:
            return message
        return f"{self.device_id}({self.device_name}): {message}"

    def send_http_log(self, message):
        """Send a log message to the HTTP endpoint"""
        if not self.http_logging_enabled:
            return False

        try:
            # Prepare JSON payload
            payload = json.dumps({"message": message})

            # Send POST request
            response = urequests.post(
                self.http_url,
                headers={"Content-Type": "application/json"},
                data=payload,
            )

            success = response.status_code == 200
            response.close()

            if not success:
                print(f"Logger: HTTP log failed with status {response.status_code}")

            return success
        except Exception as e:
            print(f"Logger: HTTP error: {e}")
            return False

    def log(self, message):
        # Always print to terminal (full message)
        formatted_msg = self.format_message(message)
        print(formatted_msg)

        # Try to display on OLED if available (truncated message)
        if self.display_manager is not None:
            try:
                truncated_msg = message[:28]  # Truncate to fit OLED
                self.display_manager.log(truncated_msg)
            except Exception as e:
                print(f"Logger: OLED error: {e}")

        # MQTT logging (full message)
        if self.mqtt_logging_enabled and self.mqtt_manager is not None:
            try:
                self.mqtt_manager.publish(self.mqtt_base_topic, formatted_msg)
            except Exception as e:
                print(f"Logger: MQTT error: {e}")

        # HTTP logging (full message)
        if self.http_logging_enabled:
            try:
                self.send_http_log(formatted_msg)
            except Exception as e:
                print(f"Logger: HTTP error: {e}")

    def set_display(self, display_manager):
        self.display_manager = display_manager
        print("Logger: Display manager set")
