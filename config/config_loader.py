# config/config_loader.py
import json
import urequests
from utils.logger import Logger


class ConfigLoader:

    def __init__(
        self,
        device_id,
        config_url="http://192.168.6.100:5000/pico_iot_config.json",
    ):
        """Initialize with device ID and URL."""
        self.device_id = device_id
        self.config_url = config_url
        self.last_timestamp = None

        self.logger = Logger.get_instance()
        self.logger.log("config_loader initialized")
        self.logger.log(f"ConfigLoader initialized for {device_id}, URL: {config_url}")

    def load_config(self):
        """Load configuration from the web server and find device-specific settings."""
        try:
            self.logger.log(f"Fetching configuration from {self.config_url}")
            response = urequests.get(self.config_url)

            if response.status_code == 200:
                self.logger.log("Config fetched successfully")
                all_config = json.loads(response.text)
                response.close()

                # Store the timestamp
                self.last_timestamp = all_config.get("timestamp", None)

                # Find device-specific configuration
                device_config = self._find_device_config(all_config)
                if device_config:
                    self.logger.log(
                        f"Found configuration for device '{self.device_id}'"
                    )

                    # Create the final configuration
                    final_config = {}

                    # Add global configurations if they exist
                    if "device_global_config" in all_config:
                        self.logger.log("Adding global device configuration")
                        device_global_config = all_config["device_global_config"]
                        final_config.update(device_global_config)
                        if "remote_logger" in device_global_config:
                            self.logger.log("Remote logger configuration found")

                    if "system_global_config" in all_config:
                        self.logger.log("Adding system global configuration")
                        final_config.update(all_config["system_global_config"])

                    # Add/override with device-specific configuration
                    self.logger.log("Adding device-specific configuration")
                    final_config.update(device_config)

                    # Ensure sensor settings are present
                    device_glob = all_config.get("device_global_config", {})
                    for key in (
                        "i2c_temp_sensor_pins",
                        "motion_sensor_pin",
                        "switch_sensor_pin",
                        "onewire_ds18b20_pin",
                    ):
                        if key in device_glob:
                            self.logger.log(
                                f"Loading '{key}' from device_global_config"
                            )
                            final_config[key] = device_glob[key]

                    return final_config
                else:
                    self.logger.log(
                        f"Device '{self.device_id}' not found in configuration"
                    )
                    raise RuntimeError(  # <-- raise so caller can reboot
                        f"Device '{self.device_id}' not found in configuration"
                    )
            else:
                self.logger.log(
                    f"Error fetching config file: HTTP status {response.status_code}"
                )
                response.close()
                raise RuntimeError(  # <-- raise on bad HTTP status
                    f"Error fetching config file: HTTP status {response.status_code}"
                )

        except Exception as e:
            raise RuntimeError(f"Error loading configuration: {e}")  # <-- raise

    def check_config(self):
        """Periodically check for config changes and reload if modified."""
        try:
            response = urequests.get(self.config_url)

            if response.status_code == 200:
                # Get the Last-Modified header
                last_modified = response.headers.get("Last-Modified", None)

                if last_modified is not None:
                    if (
                        not hasattr(self, "last_modified")
                        or self.last_modified != last_modified
                    ):
                        self.logger.log(
                            f"Change to config file! Last-Modified: {last_modified}"
                        )
                        self.last_modified = last_modified
                        response.close()
                        return self.load_config()
                    else:
                        self.logger.log("No change to config file")
                        response.close()
                        return None
                else:
                    content_text = response.text
                    new_timestamp = hash(content_text)
                    response.close()
                    if (
                        not hasattr(self, "content_hash")
                        or self.content_hash != new_timestamp
                    ):
                        self.logger.log("Configuration changed (content hash).")
                        self.content_hash = new_timestamp
                        return self.load_config()
                    else:
                        self.logger.log("Configuration unchanged (content hash)")
                        return None
            else:
                self.logger.log(
                    f"Error checking config: HTTP status {response.status_code}"
                )
                response.close()
                raise RuntimeError(  # <-- raise on bad HTTP status
                    f"Error checking config: HTTP status {response.status_code}"
                )

        except Exception as e:
            raise RuntimeError(f"Error checking configuration: {e}")  # <-- raise

    def _find_device_config(self, all_config):
        """Find device-specific configuration within the loaded data."""
        if "device_list" not in all_config:
            self.logger.log("Error: Configuration is missing 'device_list' section")
            return None

        for device in all_config["device_list"]:
            if device.get("device_id") == self.device_id:
                self.logger.log(f"Found device: {device.get('name', 'Unnamed')}")
                self.logger.log(f"Enabled: {device.get('enabled', 0)}")
                return device

        return None
