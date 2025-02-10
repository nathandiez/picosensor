import machine
import time
from bme280 import BME280

print("Starting up...")
# Initialize I2C interface (SCL=GP5, SDA=GP4)
i2c = machine.I2C(0, scl=machine.Pin(5), sda=machine.Pin(4))

# Scan for I2C devices
devices = i2c.scan()
print("I2C devices found:", devices)

if not devices:
    print("No I2C devices found! Please check your connections.")
    raise RuntimeError("BME280 not found")

if 0x76 not in devices and 0x77 not in devices:
    print("BME280 not found at expected addresses (0x76 or 0x77)")
    print("Found devices at addresses:", [hex(device) for device in devices])
    raise RuntimeError("BME280 not found at expected address")

try:
    # Initialize the BME280 sensor
    sensor = BME280(i2c=i2c)
    
    # Continuously read and print sensor values
    while True:
        try:
            # Get the temperature (F), humidity (%), and pressure (in Hg)
            temperature_f, humidity, pressure_inhg = sensor.values

            print(f"Temperature: {temperature_f:.2f} °F")
            print(f"Pressure: {pressure_inhg:.2f} in Hg")
            print(f"Humidity: {humidity:.2f} %")
            print("--------------------------")

        except Exception as e:
            print("Error reading sensor:", e)
            time.sleep(1)
            continue

        # Wait for 2 seconds before reading again
        time.sleep(2)

except KeyboardInterrupt:
    print("\nProgram stopped by user")
except Exception as e:
    print("Error initializing sensor:", e)