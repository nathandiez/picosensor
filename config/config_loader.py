# config/config_loader.py

import ujson as json
import urequests
import time
from utils.logger import Logger


class ConfigLoader:

    def __init__(
        self,
        device_id,
        config_url="http://192.168.6.132:5000/pico_iot_config.json",
    ):
        self.device_id = device_id
        self.config_url = config_url
        self.last_hash = None

        self.logger = Logger.get_instance()
        self.logger.log("ConfigLoader initialized")

    def load_config(self):
        """Fetch, parse, and process JSON configuration with retries."""
        self.logger.log(f"Fetching configuration from {self.config_url}")

        for attempt in range(3):
            try:
                current_response = None
                all_config_data = None
                try:
                    current_response = urequests.get(self.config_url, timeout=5)
                    if current_response.status_code == 200:
                        body = current_response.text
                        if not body:
                            raise RuntimeError("Empty response body")
                        all_config_data = json.loads(body)
                    else:
                        raise RuntimeError(
                            f"HTTP error: {current_response.status_code}"
                        )
                finally:
                    if current_response:
                        current_response.close()

                self.logger.log("JSON parsed successfully")
                return self._process_config(all_config_data)

            except Exception as e:
                self.logger.log(
                    f"Attempt {attempt + 1} failed: {type(e).__name__}: {e}"
                )
                if attempt < 2:
                    time.sleep(2)
                else:
                    raise  # On the last attempt, re-raise the caught exception

    def check_config(self):
        """Check for config changes via content hash and reload if necessary."""
        self.logger.log(f"Checking for configuration changes at {self.config_url}")
        try:
            current_response = None
            calculated_hash = None
            try:
                current_response = urequests.get(self.config_url, timeout=10)
                if current_response.status_code == 200:
                    config_bytes = current_response.content
                    calculated_hash = hash(config_bytes)
                else:
                    raise RuntimeError(f"HTTP error: {current_response.status_code}")
            finally:
                if current_response:
                    current_response.close()

            if calculated_hash != self.last_hash:
                self.logger.log("Configuration changed; reloading")
                self.last_hash = calculated_hash
                return self.load_config()
            else:
                self.logger.log("Configuration unchanged")
                return None

        except Exception as e:
            self.logger.log(
                f"Error during configuration check: {type(e).__name__}: {e}"
            )
            raise RuntimeError(f"Error checking configuration: {e}")

    def _process_config(self, all_config):
        """Merge global, system, and device-specific configurations."""
        device_list = all_config.get("device_list", [])
        for dev in device_list:
            if dev.get("device_id") == self.device_id:
                self.logger.log(
                    f"Found device: {dev.get('name','Unnamed')}, Enabled: {dev.get('enabled', 0)}"
                )
                final = {}

                if "device_global_config" in all_config:
                    self.logger.log("Adding device_global_config")
                    global_cfg = all_config["device_global_config"]
                    final.update(global_cfg)
                    if "remote_logger" in global_cfg:
                        self.logger.log(
                            "Remote logger configuration found in device_global_config"
                        )

                if "system_global_config" in all_config:
                    self.logger.log("Adding system_global_config")
                    final.update(all_config["system_global_config"])

                self.logger.log("Adding device-specific settings from device_list")
                final.update(dev)

                # Ensure these specific pin configurations are sourced from device_global_config
                # This allows global override/definition for these critical pin settings.
                device_global = all_config.get("device_global_config", {})
                pin_keys_to_ensure = (
                    "i2c_temp_sensor_pins",
                    "motion_sensor_pin",
                    "switch_sensor_pin",
                    "onewire_ds18b20_pin",
                )
                for key in pin_keys_to_ensure:
                    if key in device_global:
                        self.logger.log(f"Ensuring '{key}' from device_global_config")
                        final[key] = device_global[key]
                return final

        self.logger.log(f"Device_id '{self.device_id}' not found in device_list")
        raise RuntimeError(f"Device '{self.device_id}' not found in configuration")