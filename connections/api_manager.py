# connections/api_manager.py

import time
import json
import gc
import urequests
from utils.logger import Logger

class APIManager:
    def __init__(self, client_id, api_config):
        # Validate required configuration
        required_keys = ["url", "api_key", "timeout_ms"]
        missing = [key for key in required_keys if key not in api_config]
        if missing:
            raise ValueError(f"Missing required API configuration: {', '.join(missing)}")

        self.client_id = client_id
        
        # Convert HTTPS to HTTP for memory efficiency
        url = api_config["url"]
        if url.startswith("https://"):
            self.url = "http://" + url[8:]
            self.logger = Logger.get_instance()
            self.logger.log("Converting HTTPS to HTTP for memory efficiency")
        else:
            self.url = url
            
        self.api_key = api_config["api_key"]
        self.timeout_sec = api_config["timeout_ms"] / 1000.0
        self.retry_delay_ms = api_config.get("retry_delay_ms", 5000)

        # Get the shared logger instance
        self.logger = Logger.get_instance()
        self.logger.log(f"API Manager initialized for client '{self.client_id}'. URL: '{self.url}'")

    def format_payload(self, readings_dict, event_type):
        """Create minimal payload with critical data"""
        if not event_type:
            raise ValueError("Event type must be specified for API payload")

        # Create minimal dictionary with essential fields
        message = {
            "event_type": event_type,
            "device_id": self.client_id
        }

        # Add temperature (most important reading)
        temp_f = readings_dict.get("temperature_f")
        if temp_f is not None:
            try:
                message["temperature"] = round(float(temp_f), 1)
            except:
                message["temperature"] = None
        else:
            message["temperature"] = None

        # Add timestamp
        try:
            t = time.gmtime()
            message["timestamp"] = f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"
        except:
            message["timestamp"] = None

        # Add version
        message["version"] = readings_dict.get("version")

        # Add motion state if present (important for event detection)
        motion = readings_dict.get("motion")
        if motion is not None:
            message["motion"] = str(motion)

        return message

    def publish(self, readings_dict, event_type, attempt=1, max_attempts=2):
        """Memory-optimized publish method using HTTP"""
        # Force garbage collection
        gc.collect()

        try:
            # Create minimal payload
            payload_dict = self.format_payload(readings_dict, event_type)
            json_payload = json.dumps(payload_dict)
            
            # Free memory
            del payload_dict
            gc.collect()
            
            # Prepare headers - minimal
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key
            }

            self.logger.log(f"API Publish ({event_type}, attempt {attempt}/{max_attempts}) to {self.url}")

            # Make HTTP request
            response = None
            try:
                # Force garbage collection before network operation
                gc.collect()
                
                # Use shorter timeout for memory efficiency
                actual_timeout = min(5.0, self.timeout_sec)
                
                # Make the request
                response = urequests.post(
                    self.url,
                    headers=headers,
                    data=json_payload,
                    timeout=actual_timeout
                )

                # Check response
                if response.status_code == 202:
                    self.logger.log(f"API publish successful")
                    if response:
                        response.close()
                    return True
                else:
                    self.logger.log(f"API publish failed: status {response.status_code}")
                    if response:
                        response.close()
                    raise ValueError(f"Bad status: {response.status_code}")

            except Exception as e:
                if response:
                    try:
                        response.close()
                    except:
                        pass
                
                self.logger.log(f"API publish Error on attempt {attempt}: {e}")
                
                # Retry logic
                if attempt < max_attempts:
                    self.logger.log(f"Will retry API publish after {self.retry_delay_ms}ms...")
                    time.sleep_ms(self.retry_delay_ms)
                    
                    # Force garbage collection before retry
                    gc.collect()
                    
                    return self.publish(readings_dict, event_type, attempt + 1, max_attempts)
                else:
                    self.logger.log(f"API publish failed permanently after {max_attempts} attempts.")
                    return False

        except Exception as e:
            self.logger.log(f"API Publish - Error preparing request: {e}")
            return False

    def deinit(self):
        """Cleanup"""
        self.logger.log("API Manager deinitialized.")
        gc.collect()