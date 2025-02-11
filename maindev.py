import machine
import time
from bme280 import BME280

SWITCHPIN = 15
MOTIONPIN = 16

SCLPIN = 5
SDAPIN = 4

print("Starting up...")

id0_pin = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_DOWN)    
id1_pin = machine.Pin(1, machine.Pin.IN, machine.Pin.PULL_DOWN)       
id2_pin = machine.Pin(2, machine.Pin.IN, machine.Pin.PULL_DOWN)       

p0_value = id0_pin.value()
p1_value = id1_pin.value()
p2_value = id2_pin.value()

# Assuming p0_value is the least significant bit (LSB)
device_id = "pdevice" + str((p2_value << 2) | (p1_value << 1) | p0_value)

print("device_id:", device_id)

i2c = machine.I2C(0, scl=machine.Pin(SCLPIN), sda=machine.Pin(SDAPIN))
motion_pin = machine.Pin(MOTIONPIN, machine.Pin.IN, machine.Pin.PULL_DOWN)       # motion detection
switch_pin = machine.Pin(SWITCHPIN, machine.Pin.IN, machine.Pin.PULL_DOWN)     # general purpose IO monitoring
sensor = BME280(i2c=i2c)

# Continuously read and print sensor values
while True:
    # Get the temperature (F), humidity (%), and pressure (in Hg)
    temperature_f, humidity, pressure_inhg = sensor.values
    
    # Read GPIO 16 state
    switch_state = "HIGH" if switch_pin.value() == 1 else "LOW"
    motion_state = "MOTION!" if motion_pin.value() == 1 else "none"


    print(f"Temperature: {temperature_f:.2f} F")
    print(f"Pressure: {pressure_inhg:.2f} in Hg")
    print(f"Humidity: {humidity:.2f} %")
    print(f"Switch: {switch_state}")
    print(f"Motion: {motion_state}")

    print("--------------------------")
    
    # Wait for 2 seconds before reading again
    time.sleep(2)