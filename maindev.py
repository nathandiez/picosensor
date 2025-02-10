import machine
import time
from bme280 import BME280

SWITCHPIN = 15
MOTIONPIN = 16

print("Starting up...")

i2c = machine.I2C(0, scl=machine.Pin(5), sda=machine.Pin(4))

# Initialize GPIO 16 as input
gpiomotion = machine.Pin(MOTIONPIN, machine.Pin.IN, machine.Pin.PULL_DOWN)       # motion detection
gpioswitch = machine.Pin(SWITCHPIN, machine.Pin.IN, machine.Pin.PULL_UP)     # general purpose IO monitoring

sensor = BME280(i2c=i2c)

# Continuously read and print sensor values
while True:
    # Get the temperature (F), humidity (%), and pressure (in Hg)
    temperature_f, humidity, pressure_inhg = sensor.values
    
    # Read GPIO 16 state
    switch_pin = "HIGH" if gpioswitch.value() == 1 else "LOW"
    motion_pin = "HIGH" if gpiomotion.value() == 1 else "LOW"


    print(f"Temperature: {temperature_f:.2f} F")
    print(f"Pressure: {pressure_inhg:.2f} in Hg")
    print(f"Humidity: {humidity:.2f} %")
    print(f"Switch Pin: {switch_pin}")
    print(f"Motion Pin: {motion_pin}")

    print("--------------------------")
    
    # Wait for 2 seconds before reading again
    time.sleep(2)