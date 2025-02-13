# set_deviceid.py
DEVICE_ID = "kitchen_01"  # Change this to set your device ID

def write_device_id():
    try:
        with open('device_id.txt', 'w') as f:
            f.write(DEVICE_ID)
        print(f"Successfully wrote device ID: {DEVICE_ID}")
    except OSError as e:
        print(f"Error writing device ID: {e}")

if __name__ == "__main__":
    write_device_id()