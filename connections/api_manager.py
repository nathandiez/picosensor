# connections/api_manager.py

import time
import json
import gc
import urequests
from utils.logger import Logger


class APIManager:
    def __init__(self, client_id, api_config):
        # Validate required configuration
        required = ["url", "api_key", "timeout_ms"]
        missing = [k for k in required if k not in api_config]
        if missing:
            raise ValueError(f"Missing API config keys: {', '.join(missing)}")

        self.client_id = client_id
        # Force HTTP for memory efficiency
        url = api_config["url"]
        if url.startswith("https://"):
            url = "http://" + url[len("https://") :]
        self.url = url
        self.api_key = api_config["api_key"]
        self.timeout_ms = api_config["timeout_ms"]
        self.retry_delay = api_config.get("retry_delay_ms", 5000)
        self.logger = Logger.get_instance()
        self.logger.log(f"API Manager initialized for '{self.client_id}' → {self.url}")

    def publish(self, json_payload, attempt=1, max_attempts=2):
        """Publish the given JSON string via HTTP POST, retrying on failure."""
        gc.collect()
        headers = {"Content-Type": "application/json", "X-API-Key": self.api_key}

        try:
            self.logger.log(f"API Publish attempt {attempt} to {self.url}")
            resp = urequests.post(
                self.url,
                headers=headers,
                data=json_payload,
                timeout=min(5, self.timeout_ms / 1000),
            )
            status = resp.status_code
            resp.close()

            if status == 202:
                self.logger.log("API publish successful")
                return True
            else:
                self.logger.log(f"API publish failed: HTTP {status}")
                raise ValueError(f"HTTP {status}")

        except Exception as e:
            self.logger.log(f"API publish error (attempt {attempt}): {e}")
            if attempt < max_attempts:
                time.sleep_ms(self.retry_delay)
                return self.publish(json_payload, attempt + 1, max_attempts)
            return False

    def deinit(self):
        """Cleanup any persistent resources (if needed)."""
        self.logger.log("API Manager deinitialized")
        gc.collect()
