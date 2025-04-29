# utils/fan_pwm_controller.py

import machine
from utils.logger import Logger


class FanPWMController:
    """
    A controller class for managing a PWM-driven fan based on temperature readings.
    The fan speed is proportionally controlled between min and max temperature thresholds.
    """

    def __init__(self, config=None):
        """
        Initialize the fan controller with configuration settings.

        Args:
            config (dict): Configuration dictionary with fan controller settings
        """
        self.logger = Logger.get_instance()
        self.logger.log("Initializing Fan PWM Controller")

        self.enabled = False
        self.pwm = None
        self.current_duty = 0
        self.last_temperature = None

        # Configure with provided settings if available
        if config:
            self.configure(config)

    def configure(self, config):
        """Configure the fan controller with settings from the config dictionary."""
        # Get fan controller config without default
        fan_config = config.get("fan_pwm_controller_config")
        if fan_config is None:
            raise ValueError("Missing fan_pwm_controller_config in configuration")

        # Validate all required keys are present
        required_keys = [
            "enabled",
            "manual_override",
            "pwm_pin",
            "pwm_freq",
            "temp_min",
            "temp_max",
            "fan_min_duty",
            "fan_max_duty",
            "hysteresis",
        ]
        missing = [key for key in required_keys if key not in fan_config]
        if missing:
            raise ValueError(
                f"Missing required fan controller configuration: {', '.join(missing)}"
            )

        # Extract configuration values without defaults
        self.enabled = fan_config["enabled"]
        manual = fan_config["manual_override"]
        self.manual_override_enabled = manual.get("enabled", False)
        self.manual_dutycycle = manual.get("manual_dutycycle", 0)
        self.pwm_pin = fan_config["pwm_pin"]
        self.pwm_freq = fan_config["pwm_freq"]
        self.temp_min = fan_config["temp_min"]
        self.temp_max = fan_config["temp_max"]
        self.fan_min_duty = fan_config["fan_min_duty"]
        self.fan_max_duty = fan_config["fan_max_duty"]
        self.hysteresis = fan_config["hysteresis"]

        self.logger.log(
            f"Fan pwm controller config: enabled={self.enabled}, pin={self.pwm_pin}"
        )
        self.logger.log(f"Temperature range: {self.temp_min}C to {self.temp_max}C")

        # Initialize PWM if enabled
        if self.enabled:
            if not self.initialize_pwm():
                raise RuntimeError("Failed to initialize PWM for fan controller")
        else:
            self.stop()

    def initialize_pwm(self):
        """Initialize the PWM output on the configured pin."""
        try:
            # Clean up any existing PWM
            if self.pwm:
                self.pwm.deinit()

            # Set up new PWM on configured pin
            pwm_pin = machine.Pin(self.pwm_pin, machine.Pin.OUT)
            self.pwm = machine.PWM(pwm_pin)
            self.pwm.freq(self.pwm_freq)

            # Start with fan off
            self.set_duty(0)
            self.logger.log(
                f"PWM initialized on pin {self.pwm_pin} at {self.pwm_freq}Hz"
            )
            return True

        except Exception as e:
            self.logger.log(f"PWM initialization failed: {e}")
            self.pwm = None
            return False

    def update(self, temperature_c):
        if not self.enabled or self.pwm is None:
            return 0

        # Check for fixed duty override
        if self.manual_override_enabled:
            fixed_duty = max(0, min(100, self.manual_dutycycle))
            if fixed_duty != self.current_duty:
                self.set_duty(fixed_duty)
                self.logger.log(f"pwm fan duty manually overridden to {fixed_duty}%")
            return self.current_duty

        # Proceed with temperature-based control
        self.last_temperature = temperature_c

        if self.current_duty == 0 and temperature_c < (self.temp_min + self.hysteresis):
            new_duty = 0
        elif self.current_duty > 0 and temperature_c < (
            self.temp_min - self.hysteresis
        ):
            new_duty = 0
        elif temperature_c >= self.temp_max:
            new_duty = self.fan_max_duty
        elif temperature_c <= self.temp_min:
            new_duty = 0
        else:
            temp_range = self.temp_max - self.temp_min
            temp_factor = (temperature_c - self.temp_min) / temp_range
            duty_range = self.fan_max_duty - self.fan_min_duty
            new_duty = int(temp_factor * duty_range) + self.fan_min_duty

        if new_duty != self.current_duty:
            self.set_duty(new_duty)
            self.logger.log(f"Fan pwm duty: {new_duty}% at temp: {temperature_c}C")

        return self.current_duty

    def set_duty(self, duty_cycle):
        """
        Set PWM duty cycle with gamma correction for any perceived nonlinearity
        """
        if not self.enabled or self.pwm is None:
            self.current_duty = 0
            return

        # Ensure duty cycle is within valid range
        duty_cycle = max(0, min(100, duty_cycle))

        # Apply gamma correction if needed
        gamma = 1.0
        normalized = duty_cycle / 100.0
        corrected = normalized**gamma

        # Convert to PWM value (0-65535)
        pwm_value = int(corrected * 65535)

        # Set the PWM duty cycle
        self.pwm.duty_u16(pwm_value)
        self.current_duty = duty_cycle

    def start(self):
        """Start the fan at minimum speed."""
        if self.enabled and self.pwm is not None:
            self.set_duty(self.fan_min_duty)

    def stop(self):
        """Stop the fan."""
        if self.pwm is not None:
            self.set_duty(0)

    def deinit(self):
        """Clean up resources."""
        self.stop()
        if self.pwm is not None:
            try:
                self.pwm.deinit()
                self.pwm = None
            except:
                pass
