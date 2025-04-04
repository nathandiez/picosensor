# utils/device_id.py
import machine

def get_device_id():
    try:
        with open('device_id.txt', 'r') as f:
            device_id_str = f.readline().strip()
            if device_id_str: return device_id_str
            else: print("Warning: device_id.txt is empty!")
    except OSError:
        print("Warning: device_id.txt not found!")
    print("Using unique machine ID as device ID.")
    try: return machine.unique_id().hex()
    except AttributeError:
        print("Error: Cannot get unique machine ID.")
        return "unknown_pico_device"

def is_dev_mode():
    try:
        with open('device_id.txt', 'r') as f:
            lines = f.readlines()
            if len(lines) >= 2 and 'dev' in lines[1].lower():
                return True
    except OSError:
        pass
    return False