# config/config_loader.py

import ujson as json
import usocket
from utils.logger import Logger


class ConfigLoader:

    def __init__(
        self,
        device_id,
        config_url="http://iotv2devstorage.blob.core.windows.net/configs/pico_iot_config.json",
    ):
        """Initialize with device ID and URL."""
        self.device_id = device_id
        self.config_url = config_url
        self.last_hash = None

        self.logger = Logger.get_instance()
        self.logger.log("config_loader initialized")
        self.logger.log(f"ConfigLoader initialized for {device_id}, URL: {config_url}")

    def load_config(self):
        """Fetch & parse JSON via HTTP/1.1 socket, then merge into final_config."""
        try:
            self.logger.log(f"Fetching configuration from {self.config_url}")
            # break out host + path
            url = self.config_url.split("://", 1)[1]
            host, path = url.split("/", 1) if "/" in url else (url, "")
            path = "/" + path

            # open socket
            addr = usocket.getaddrinfo(host, 80)[0][-1]
            s = usocket.socket()
            s.connect(addr)
            # send HTTP/1.1 GET
            s.write(
                b"GET " + path.encode() + b" HTTP/1.1\r\n"
                b"Host: " + host.encode() + b"\r\n"
                b"Connection: close\r\n\r\n"
            )

            # check status
            status = s.readline()
            if b"200" not in status:
                s.close()
                raise RuntimeError(f"HTTP error: {status}")

            # skip headers
            while True:
                line = s.readline()
                if not line or line == b"\r\n":
                    break

            # read body
            body = b""
            while True:
                chunk = s.read(512)
                if not chunk:
                    break
                body += chunk
            s.close()

            all_config = json.loads(body)
            return self._process_config(all_config)

        except Exception as e:
            raise RuntimeError(f"Error loading configuration: {e}")

    def check_config(self):
        """
        Check for a changed payload (by simple content hash) and reload if changed.
        Returns new config dict if it changed, else None.
        """
        try:
            # Fetch raw bytes same as load_config but only to compare hash
            url = self.config_url.split("://", 1)[1]
            host, path = url.split("/", 1) if "/" in url else (url, "")
            path = "/" + path

            addr = usocket.getaddrinfo(host, 80)[0][-1]
            s = usocket.socket()
            s.connect(addr)
            s.write(
                b"GET " + path.encode() + b" HTTP/1.1\r\n"
                b"Host: " + host.encode() + b"\r\n"
                b"Connection: close\r\n\r\n"
            )

            # skip status + headers
            s.readline()
            while True:
                line = s.readline()
                if not line or line == b"\r\n":
                    break

            # read body
            body = b""
            while True:
                chunk = s.read(512)
                if not chunk:
                    break
                body += chunk
            s.close()

            new_hash = hash(body)
            if new_hash != self.last_hash:
                self.logger.log("Configuration changed; reloading")
                self.last_hash = new_hash
                return self.load_config()
            else:
                self.logger.log("Configuration unchanged")
                return None

        except Exception as e:
            raise RuntimeError(f"Error checking configuration: {e}")

    def _process_config(self, all_config):
        """Merge global, system, and device-specific configurations."""
        # find your device in device_list
        device_list = all_config.get("device_list", [])
        for dev in device_list:
            if dev.get("device_id") == self.device_id:
                self.logger.log(f"Found device: {dev.get('name','Unnamed')}")
                self.logger.log(f"Enabled: {dev.get('enabled', 0)}")
                final = {}

                # global device config
                if "device_global_config" in all_config:
                    self.logger.log("Adding global device configuration")
                    global_cfg = all_config["device_global_config"]
                    final.update(global_cfg)
                    if "remote_logger" in global_cfg:
                        self.logger.log("Remote logger configuration found")

                # system global config
                if "system_global_config" in all_config:
                    self.logger.log("Adding system global configuration")
                    final.update(all_config["system_global_config"])

                # device-specific
                self.logger.log("Adding device-specific configuration")
                final.update(dev)

                # ensure pins
                device_global = all_config.get("device_global_config", {})
                for key in (
                    "i2c_temp_sensor_pins",
                    "motion_sensor_pin",
                    "switch_sensor_pin",
                    "onewire_ds18b20_pin",
                ):
                    if key in device_global:
                        self.logger.log(f"Loading '{key}'")
                        final[key] = device_global[key]

                return final

        # not found
        self.logger.log(f"Device '{self.device_id}' not found")
        raise RuntimeError(f"Device '{self.device_id}' not found")
