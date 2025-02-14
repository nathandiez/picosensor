import machine
import time
from bme280 import BME280
import network
from lib.umqtt.simple import MQTTClient

# Constants
SWITCHPIN = 15
MOTIONPIN = 16
SCLPIN = 5
SDAPIN = 4
MQTT_BROKER = "35.185.14.240"  # Replace with the IP of your Mosquitto broker if needed
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/reading"

print("Starting up...")

# Get device ID from filesystem
def get_device_id():
    try:
        with open('device_id.txt', 'r') as f:
            device_id = f.read().strip()
            return device_id
    except OSError:
        print("Warning: No device ID found! Please run set_deviceid.py first")
        return "pdevice_unknown"  # Fallback ID

device_id = get_device_id()
print("device_id:", device_id)

# Set up I2C and sensor
i2c = machine.I2C(0, scl=machine.Pin(SCLPIN), sda=machine.Pin(SDAPIN))
motion_pin = machine.Pin(MOTIONPIN, machine.Pin.IN, machine.Pin.PULL_DOWN)       # motion detection
switch_pin = machine.Pin(SWITCHPIN, machine.Pin.IN, machine.Pin.PULL_DOWN)     # general purpose IO monitoring
sensor = BME280(i2c=i2c)

# Set up Wi-Fi connection (assuming you're using Wi-Fi for MQTT)
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect('Mesh-678', 'DaisyRabbit')  
    while not wlan.isconnected():
        time.sleep(1)
    print('Connected to Wi-Fi:', wlan.ifconfig())

# MQTT setup
def mqtt_connect():
    client = MQTTClient(device_id, MQTT_BROKER, port=MQTT_PORT)
    client.connect()
    return client

# Main loop
def main():
    # Connect to Wi-Fi and MQTT
    print("about to connect to wifi")
    connect_wifi()
    print("about to connect to mqtt")
    mqtt_client = mqtt_connect()

    # Continuously read and publish sensor values
    while True:
        # Get sensor readings
        temperature_f, humidity, pressure_inhg = sensor.values
        
        # Read GPIO state
        switch_state = "HIGH" if switch_pin.value() == 1 else "LOW"
        motion_state = "MOTION!" if motion_pin.value() == 1 else "none"
        
        # Format message
        message = {
            "temperature_f": temperature_f,
            "humidity": humidity,
            "pressure_inhg": pressure_inhg,
            "switch_state": switch_state,
            "motion_state": motion_state
        }

        # Publish message to MQTT broker
        mqtt_client.publish(MQTT_TOPIC, str(message))
        
        # Print data
        print(f"Sent: {message}")
        
        # Wait before next reading
        time.sleep(5)

if __name__ == "__main__":
    main()