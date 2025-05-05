# utils/uptime_tracker.py
import time


class UptimeTracker:
    """
    Tracks device uptime with protection against counter overflow.
    Provides uptime in "dd:hh:mm:ss" format.
    """

    def __init__(self):
        """Initialize a new uptime tracker"""
        self.days = 0
        self.start_time_ms = time.ticks_ms()
        self.last_check_time = self.start_time_ms

    def update(self):
        """
        Update the uptime tracker, handling potential overflows.
        Call this method regularly in the main application loop.
        """
        current_time = time.ticks_ms()

        # Calculate the elapsed time since last check
        elapsed_ms = time.ticks_diff(current_time, self.last_check_time)

        # If elapsed time is negative, we might have had an overflow
        if elapsed_ms < 0:
            # Handle overflow by resetting start time
            self.start_time_ms = current_time
        else:
            # Convert elapsed time to hours
            elapsed_hours = elapsed_ms // 3600000  # ms to hours

            # If more than 24 hours have passed, increment days
            if elapsed_hours >= 24:
                days_to_add = elapsed_hours // 24
                self.days += days_to_add

                # Reset start time to account for the days we just added
                hours_to_subtract = days_to_add * 24
                ms_to_subtract = hours_to_subtract * 3600000
                self.start_time_ms = time.ticks_add(self.start_time_ms, ms_to_subtract)

        # Update last check time
        self.last_check_time = current_time

    def get_uptime_string(self):
        """
        Returns uptime as a formatted string in "dd:hh:mm:ss" format

        Returns:
            str: Formatted uptime string
        """
        current_time = time.ticks_ms()

        # Calculate milliseconds of uptime
        total_ms = time.ticks_diff(current_time, self.start_time_ms)

        # Calculate hours, minutes and seconds
        hours = (total_ms // 3600000) % 24  # ms to hours, modulo 24
        minutes = (total_ms // 60000) % 60  # ms to minutes, modulo 60
        seconds = (total_ms // 1000) % 60  # ms to seconds, modulo 60

        # Format as "dd:hh:mm:ss"
        return f"{self.days:02d}:{hours:02d}:{minutes:02d}:{seconds:02d}"
