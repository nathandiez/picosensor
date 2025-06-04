# main.py

import machine
import time

# Set to True for development mode, False for production
# DEV_MODE = True
DEV_MODE = False

if DEV_MODE:
    print(
        "Running in DEVELOPMENT mode - exiting main.py.  Run app.py to start the application."
    )
else:
    print("Running in PRODUCTION mode - launching application")
    try:
        # import your bootstrap and runtime functions
        from app import bootstrap
        from runtime import run_loop

        # initialize everything and enter the main loop
        state = bootstrap()
        run_loop(state)

    except Exception as e:
        print(f"Application error: {e}")
        print("Rebooting in 30 seconds...")
        # pause before reset to give you a chance to read the error
        time.sleep_ms(30000)
        machine.reset()