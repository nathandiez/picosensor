# main.py
import machine
import time
from utils.device_id import get_device_id, is_dev_mode

if is_dev_mode():
    print(f"Device '{get_device_id()}' running in DEVELOPMENT mode")
    # Development mode - don't auto-start application
else:
    print(f"Device '{get_device_id()}' running in PRODUCTION mode")
    # Production mode - auto-start application
    try:
        import app
        app.run_application()
    except Exception as e:
        print(f"Application error: {e}")
        print("Rebooting in 30 seconds...")
        time.sleep_ms(30000)
        machine.reset()