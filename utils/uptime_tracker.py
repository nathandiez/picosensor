# utils/uptime_tracker.py

import time


class UptimeTracker:
    """
    Tracks device uptime with protection against counter overflow.
    Provides uptime in "dd:hh:mm:ss" format and total seconds.
    """

    def __init__(self):
        self.days = 0
        self.start_time_ms = time.ticks_ms()
        self.last_check_time = self.start_time_ms

    def update(self):
        current_time = time.ticks_ms()
        elapsed_ms = time.ticks_diff(current_time, self.last_check_time)
        if elapsed_ms < 0:
            # overflow
            self.start_time_ms = current_time
        else:
            elapsed_hours = elapsed_ms // 3600000
            if elapsed_hours >= 24:
                days_to_add = elapsed_hours // 24
                self.days += days_to_add
                ms_to_subtract = days_to_add * 24 * 3600000
                self.start_time_ms = time.ticks_add(self.start_time_ms, ms_to_subtract)
        self.last_check_time = current_time

    def get_uptime_string(self):
        current_time = time.ticks_ms()
        total_ms = time.ticks_diff(current_time, self.start_time_ms)
        hours = (total_ms // 3600000) % 24
        minutes = (total_ms // 60000) % 60
        seconds = (total_ms // 1000) % 60
        return f"{self.days:02d}:{hours:02d}:{minutes:02d}:{seconds:02d}"

    def get_uptime_seconds(self):
        """
        Returns the total uptime in seconds (including full days).
        """
        current_time = time.ticks_ms()
        total_ms = (
            time.ticks_diff(current_time, self.start_time_ms) + self.days * 24 * 3600000
        )
        return total_ms // 1000
