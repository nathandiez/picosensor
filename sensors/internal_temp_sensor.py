import machine
import time

class InternalTempSensor:
    def __init__(self, config=None):
        self.sensor = machine.ADC(4)
        self.calibration_offset = -12.0  # Adjust based on actual comparison

    def read_values(self, samples=10, delay_ms=10):
        readings = []
        for _ in range(samples):
            adc = self.sensor.read_u16()
            readings.append(adc)
            time.sleep_ms(delay_ms)
        avg_adc = sum(readings) / len(readings)
        voltage = avg_adc * (3.3 / 65535)
        temperature_c = 27 - (voltage - 0.706) / 0.001721
        temperature_f = temperature_c * 9 / 5 + 32 + self.calibration_offset
        return temperature_f
