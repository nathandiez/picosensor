# main.py
import machine
import time

# Set to True for development mode, False for production
DEV_MODE = True
# DEV_MODE = False

if DEV_MODE:
    print("Running in DEVELOPMENT mode - exiting main.py.  Run app.py to start the application.")
    # Development mode - don't auto-start application
else:
    print("Running in PRODUCTION mode - launching application")
    # Production mode - auto-start application
    try:
        import app
        app.run_application()
    except Exception as e:
        print(f"Application error: {e}")
        print("Rebooting in 30 seconds...")
        time.sleep_ms(30000)
        machine.reset()