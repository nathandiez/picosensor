import time
import json
from collections import OrderedDict


class PayloadFormatter:
    @staticmethod
    def mqtt_payload(client_id, readings, event_type):
        if not event_type:
            raise ValueError("Event type must be specified")

        msg = OrderedDict()
        msg["event_type"] = event_type
        msg["device_id"] = client_id

        # Sensor values
        temp = readings.get("temperature_f")
        msg["temperature"] = round(float(temp), 1) if temp is not None else None

        hum = readings.get("humidity")
        msg["humidity"] = round(float(hum), 1) if hum is not None else None

        pres = readings.get("pressure_inhg")
        msg["pressure"] = round(float(pres), 2) if pres is not None else None

        msg["motion"] = str(readings.get("motion"))
        msg["switch"] = str(readings.get("switch"))

        # Add sensor_type field
        msg["sensor_type"] = readings.get("temp_sensor_type", "UNKNOWN")

        # New fields
        msg["wifi_rssi"] = readings.get("wifi_rssi")
        msg["uptime_seconds"] = readings.get("uptime_seconds")
        msg["fan_pwm"] = readings.get("fan_pwm")
        msg["fans_active_level"] = readings.get("fans_active_level")

        # Timestamp UTC ISO8601
        t = time.localtime()
        msg["timestamp"] = (
            f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"
        )

        # Extras
        msg["version"] = readings.get("version")
        msg["uptime"] = readings.get("uptime")

        return json.dumps(msg)

    @staticmethod
    def api_payload(client_id, readings, event_type):
        if not event_type:
            raise ValueError("Event type must be specified")

        payload = {
            "event_type": event_type,
            "device_id": client_id,
            "temperature": (
                round(float(readings.get("temperature_f")), 1)
                if readings.get("temperature_f") is not None
                else None
            ),
            # Add sensor_type to API payload as well
            "sensor_type": readings.get("temp_sensor_type", "UNKNOWN"),
            # include extras if you want them in API too
            "wifi_rssi": readings.get("wifi_rssi"),
            "uptime_seconds": readings.get("uptime_seconds"),
            "fan_pwm": readings.get("fan_pwm"),
            "fans_active_level": readings.get("fans_active_level"),
        }
        t = time.gmtime()
        payload["timestamp"] = (
            f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"
        )
        payload["version"] = readings.get("version")
        return json.dumps(payload)