# config/settings.py

WIFI_CONFIG = {
    "ENABLED": True,
    "SSID": "Mesh-678",  # Your WiFi SSID
    "PASSWORD": "DaisyRabbit" # Your WiFi Password
}

# MQTT_CONFIG = {
#     "ENABLED": True,
#     # --- Update these values ---
#     "BROKER": "35.196.92.117", # Use the LoadBalancer IP
#     "PORT": 8883,                             # TLS Port
#     "USER": "pico_device",                # <<< CHANGE THIS to your Pico's username
#     "PASSWORD": "pico_pw123",          # <<< CHANGE THIS to your Pico's password
#     "BASE_TOPIC": "home/sensors",             # Base topic (device ID will be appended)
#     "SSL": True,                              # Enable TLS/SSL
#     "SSL_PARAMS": {"ca_certs": "ca.crt"}      # Path to CA cert on Pico filesystem
#     # --- End of updates ---
# }

#  Unfortunately the latest off-the-shelf micropython MQTT library does not support SSL.
# To-Do is to possibly build a custom MQTT library that supports SSL.
MQTT_CONFIG = {
    "ENABLED": True,
    # --- Update these values ---
    "BROKER": "35.243.252.129", # Use the LoadBalancer IP
    "PORT": 1883,                             # non-TLS Port
    "USER": "pico_device",                # <<< CHANGE THIS to your Pico's username
    "PASSWORD": "pico_pw123",          # <<< CHANGE THIS to your Pico's password
    "BASE_TOPIC": "home/sensors",             # Base topic (device ID will be appended)
    "SSL": False,                              # Disable TLS/SSL
    # "SSL_PARAMS": {"ca_certs": "ca.crt"}      # Path to CA cert on Pico filesystem
    # --- End of updates ---
}

TEMP_SENSOR_PINS = {
    "I2C_SCL": 5,
    "I2C_SDA": 4,
}

MOTION_SENSOR_PIN = {
    "PIN": 16
}

SWITCH_SENSOR_PIN = {
    "PIN": 15
}

# Time constants in milliseconds
MAIN_LOOP_DELAY = 30000      # 30 seconds
MQTT_RECONNECT_DELAY = 10000 # 10 seconds
MOTION_WAIT_PERIOD = 30000   # 30 seconds
MOTION_CHECK_INTERVAL = 1000  # 1 second
SWITCH_CHECK_INTERVAL = 1000  # 1 second
TEMPERATURE_CHECK_INTERVAL = 5000  # 5 seconds