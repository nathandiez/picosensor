# utils/ntp_time.py
import ntptime
import time


class NTPClock:
    """
    NTPClock class for synchronizing the internal RTC with an NTP server.
    Optionally applies an offset (in seconds) to convert UTC to local time.
    For EST (Eastern Standard Time), use an offset of -5*3600 (i.e., -18000 seconds).
    """

    def __init__(self, server="pool.ntp.org", offset=-5 * 3600):
        self.server = server
        self.offset = offset

    def sync(self):
        try:
            ntptime.host = self.server
            ntptime.settime()  # Sets the RTC to UTC
            return True
        except Exception as e:
            print("NTP sync failed:", e)
            return False

    def get_time_str(self):
        """
        Return the current time as a formatted string adjusted by the offset.
        For EST, this converts UTC to Eastern Standard Time.
        """
        # Get the current UTC time tuple.
        t = time.localtime()
        # Convert the tuple to seconds since epoch.
        seconds = time.mktime(t)
        # Apply the offset (for EST, offset is -5*3600).
        local_seconds = seconds + self.offset
        # Convert back to a time tuple.
        local_time = time.localtime(local_seconds)
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            local_time[0],
            local_time[1],
            local_time[2],
            local_time[3],
            local_time[4],
            local_time[5],
        )
