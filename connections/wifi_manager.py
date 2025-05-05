# wifi_manager.py

import network
import time
from utils.ntp_time import NTPClock
from utils.logger import Logger


class WiFiManager:
    def __init__(
        self, time_offset=-4 * 3600
    ):  # To-do is to replace this hardcoded offset with a better solution
        self.ssid = "Mesh-678"
        self.password = "DaisyRabbit"
        self.ntp_host = "time.google.com"  # Changed from "pool.ntp.org"
        self.time_offset = time_offset
        self.wlan = network.WLAN(network.STA_IF)
        self.ntp_synced = False
        self.ntp_time = None

        self.logger = Logger.get_instance()
        self.logger.log("wifi Manager initialized")

    def connect(self):
        self.logger.log("Connecting to WiFi...")
        if self.wlan.isconnected():
            self.logger.log("Already connected.")
            if not self.ntp_synced:  # Sync time if reconnecting without reboot
                self._sync_time()
            return True

        self.wlan.active(True)
        self.wlan.connect(self.ssid, self.password)

        # Wait for connection with a timeout
        max_wait = 15
        while max_wait > 0:
            if self.wlan.status() < 0 or self.wlan.status() >= 3:
                break  # Connection attempt finished (success or fail)
            max_wait -= 1
            print("Waiting for WiFi connection...")
            time.sleep(1)

        if self.wlan.isconnected():
            self.logger.log("WiFi Connected.")
            self.logger.log(f"IP Config: {self.wlan.ifconfig()}")
            self._sync_time()
            return True
        else:
            self.logger.log("WiFi connection failed.")
            self.wlan.active(False)  # Turn off WLAN if connect failed
            raise RuntimeError("WiFi connection failed")

    def _sync_time(self):
        self.logger.log(f"Attempting NTP time sync with {self.ntp_host}...")
        try:
            self.ntp_time = NTPClock(self.ntp_host, offset=self.time_offset)
            result = self.ntp_time.sync()
            self.logger.log(f"NTP sync result: {result}")
            if result is True:
                self.ntp_synced = True
                print("Time after NTP sync:", self.ntp_time.get_time_str())
            else:
                raise RuntimeError("NTP sync failed (sync() returned non-True value)")
        except Exception as e:
            raise RuntimeError(f"NTP sync raised exception: {e}")

    def is_connected(self):
        return self.wlan.isconnected()

    def ensure_connected(self):
        if not self.is_connected():
            return self.connect()
        return True

    def get_rssi(self):
        if self.is_connected():
            try:
                return self.wlan.status("rssi")
            except Exception:
                return None
        return None

    def disconnect(self):
        if self.wlan.isconnected():
            self.wlan.disconnect()
        self.wlan.active(False)
        self.logger.log("WiFi disconnected.")

    def get_current_time(self):
        """Return the current time string using NTP clock if available"""
        if self.ntp_time:
            return self.ntp_time.get_time_str()
        return None
