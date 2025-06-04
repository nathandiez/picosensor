# utils/device_id.py
from machine import Pin


def get_device_id():
    """
    Read device ID from GPIO pins 0-3 and return a human-readable device ID
    in the format "LocationNN" where NN is the numeric ID (00-15)
    """
    # Define the pins to use for device ID
    id_pins = [
        Pin(0, Pin.IN, Pin.PULL_DOWN),  # Bit 0 (LSB)
        Pin(1, Pin.IN, Pin.PULL_DOWN),  # Bit 1
        Pin(2, Pin.IN, Pin.PULL_DOWN),  # Bit 2
        Pin(3, Pin.IN, Pin.PULL_DOWN),  # Bit 3 (MSB)
    ]

    # Calculate the binary value (0-15)
    binary_id = 0
    for i, pin in enumerate(id_pins):
        try:
            value = int(pin.value())  # Ensure it's a plain int, not a tuple
        except Exception as e:
            print(f"Error reading pin {i}: {e}")
            value = 0
        if value:  # Pin is HIGH (connected to 3.3V)
            binary_id |= 1 << i

    # Map binary IDs to locations
    id_map = {
        0: "Office",
        1: "Exterior",
        2: "Garage",
        3: "MasterBed",
        4: "LivingRoom",
        5: "Basement",
        6: "Attic",
        7: "FrontDoor",
        8: "BackDoor",
        9: "GuestRoom",
        10: "Bathroom",
        11: "Patio",
        12: "Hallway",
        13: "DiningRoom",
        14: "Laundry",
        15: "Spare",
    }

    # Get the location name from the map
    location = id_map.get(binary_id, "Unknown")

    # Format the device ID as "LocationNN"
    device_id = f"{location}{binary_id:02d}"

    # Debug output
    pin_values = [int(pin.value()) for pin in id_pins]
    try:
        print(
            f"Device ID pins: {pin_values} (binary: {''.join(str(b) for b in reversed(pin_values))})"
        )
    except Exception as e:
        print(f"Error printing pin values: {e} (values: {pin_values})")

    print(f"Numeric ID: {binary_id}")
    # print(f"Device ID: {device_id}")

    return device_id