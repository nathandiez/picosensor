# utils/fan_step_controller.py

import machine
from utils.logger import Logger


class FanStepController:
    """
    A controller class for managing multiple fans based on temperature readings.
    Fans are turned on/off sequentially as temperature rises or falls.
    """

    def __init__(self, config=None):
        """
        Initialize the fan step controller with configuration settings.

        Args:
            config (dict): Configuration dictionary with fan controller settings
        """
        self.logger = Logger.get_instance()
        self.logger.log("Initializing Fan Step Controller")

        self.enabled = False
        self.fan_pins = []
        self.active_fans = 0
        self.total_fans = 0
        self.last_temperature = None
        self.fan_step_thresholds = []
        self.temp_step_size = None

        # Configure with provided settings if available
        if config:
            self.configure(config)

    def configure(self, config):
        """Configure the fan step controller with settings from the config dictionary."""
        # Get fan controller config without default
        fan_config = config.get("fan_step_controller_config")
        if fan_config is None:
            raise ValueError("Missing fan_step_controller_config in configuration")

        # Validate all required keys are present
        required_keys = [
            "enabled",
            "manual_override",
            "pins",
            "temp_min",
            "temp_max",
            "hysteresis",
        ]
        missing = [key for key in required_keys if key not in fan_config]
        if missing:
            raise ValueError(
                f"Missing required fan step controller configuration: {', '.join(missing)}"
            )

        # Extract configuration values
        self.enabled = fan_config["enabled"]
        manual = fan_config["manual_override"]
        self.manual_override_enabled = manual.get("enabled", False)
        self.manual_fans_active = manual.get("fans_active", 0)
        self.pin_numbers = fan_config["pins"]
        self.temp_min = fan_config["temp_min"]
        self.temp_max = fan_config["temp_max"]
        self.hysteresis = fan_config["hysteresis"]

        # Get optional temp_step_size from config
        self.temp_step_size = fan_config.get("temp_step_size")

        # Initialize fan pins
        self.fan_pins = []
        self.total_fans = len(self.pin_numbers)

        # Calculate temperature thresholds for each fan
        self._calculate_thresholds()

        self.logger.log(
            f"Fan step controller config: enabled={self.enabled}, pins={self.pin_numbers}"
        )
        self.logger.log(f"Temperature range: {self.temp_min}C to {self.temp_max}C")
        if self.temp_step_size is not None:
            self.logger.log(f"Step size: {self.temp_step_size:.2f}C")
        self.logger.log(f"Fan thresholds: {self.fan_step_thresholds}")

        # Initialize pins if enabled
        if self.enabled:
            if not self.initialize_pins():
                raise RuntimeError("Failed to initialize pins for fan step controller")
        else:
            self.stop()

    def _calculate_thresholds(self):
        """Calculate the temperature thresholds for activating each fan."""
        self.fan_step_thresholds = []

        if self.total_fans > 0:
            temp_range = self.temp_max - self.temp_min

            # If temp_step_size was not provided, calculate it
            if self.temp_step_size is None:
                # Calculate step size based on temperature range and number of fans
                self.temp_step_size = temp_range / (self.total_fans + 1)
                self.logger.log(f"Calculated step size: {self.temp_step_size:.2f}C")

            # Calculate threshold for each fan
            for i in range(self.total_fans):
                # Evenly distribute thresholds across the temperature range
                threshold = self.temp_min + (i + 1) * self.temp_step_size
                # Ensure last fan doesn't exceed max temp
                if threshold > self.temp_max:
                    threshold = self.temp_max
                self.fan_step_thresholds.append(threshold)

    def initialize_pins(self):
        """Initialize the digital output pins for all fans."""
        try:
            # Clean up any existing pins
            self.fan_pins = []

            # Set up new pins
            for pin_number in self.pin_numbers:
                pin = machine.Pin(pin_number, machine.Pin.OUT)
                pin.value(0)  # Start with fan off
                self.fan_pins.append(pin)

            self.logger.log(f"Initialized {len(self.fan_pins)} fan pins")
            return True

        except Exception as e:
            self.logger.log(f"Fan pins initialization failed: {e}")
            self.fan_pins = []
            return False

    def update(self, temperature_c):
        """
        Update fan states based on current temperature.

        Args:
            temperature_c (float): Current temperature in Celsius

        Returns:
            int: Number of active fans
        """
        if not self.enabled or not self.fan_pins:
            return 0

        # Save the current temperature
        self.last_temperature = temperature_c

        # Check for manual override
        if self.manual_override_enabled:
            fans_to_enable = max(0, min(self.total_fans, self.manual_fans_active))
            if fans_to_enable != self.active_fans:
                self.set_active_fans(fans_to_enable)
                self.logger.log(f"Fans manually overridden to {fans_to_enable} active")
            return self.active_fans

        # Calculate how many fans should be active based on temperature
        fans_to_enable = 0

        # Apply hysteresis to prevent rapid fan cycling
        if self.active_fans > 0:
            # For decreasing temperature, use lower threshold (hysteresis)
            for i, threshold in enumerate(self.fan_step_thresholds):
                if temperature_c >= (threshold - self.hysteresis):
                    fans_to_enable = i + 1
        else:
            # For increasing temperature from zero, use regular thresholds
            for i, threshold in enumerate(self.fan_step_thresholds):
                if temperature_c >= threshold:
                    fans_to_enable = i + 1

        # Ensure we don't exceed the number of available fans
        fans_to_enable = min(fans_to_enable, self.total_fans)

        # Set fans if the count has changed
        if fans_to_enable != self.active_fans:
            self.set_active_fans(fans_to_enable)
            self.logger.log(f"Active fans: {fans_to_enable} at temp: {temperature_c}C")

        return self.active_fans

    def set_active_fans(self, count):
        """
        Set the number of active fans.

        Args:
            count (int): Number of fans to activate (0 to total_fans)
        """
        if not self.enabled or not self.fan_pins:
            self.active_fans = 0
            return

        # Ensure count is within valid range
        count = max(0, min(self.total_fans, count))

        # Turn on/off each fan as needed
        for i, pin in enumerate(self.fan_pins):
            if i < count:
                pin.value(1)  # Turn on
            else:
                pin.value(0)  # Turn off

        self.active_fans = count

    def start(self):
        """Enable all fans."""
        if self.enabled and self.fan_pins:
            self.set_active_fans(self.total_fans)
            self.logger.log("All fans started")

    def stop(self):
        """Stop all fans."""
        if self.fan_pins:
            self.set_active_fans(0)
            self.logger.log("All fans stopped")

    def deinit(self):
        """Clean up resources."""
        self.stop()
        self.fan_pins = []
        self.logger.log("Fan step controller deinitialized")
