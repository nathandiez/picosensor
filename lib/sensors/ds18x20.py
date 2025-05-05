# MicroPython DS18x20 temperature sensor driver
# MIT license; Copyright (c) 2016 Damien P. George

from micropython import const

_CONVERT = const(0x44)
_RD_SCRATCHPAD = const(0xbe)
_WR_SCRATCHPAD = const(0x4e)
_COPY_SCRATCHPAD = const(0x48)
_RD_POWER_SUPPLY = const(0xb4)
_SKIP_ROM = const(0xcc)

class DS18X20:
    def __init__(self, onewire):
        self.ow = onewire
        self.buf = bytearray(9)
        self.config = bytearray(3)

    def scan(self):
        return [rom for rom in self.ow.scan() if rom[0] in (0x10, 0x22, 0x28)]

    def convert_temp(self):
        self.ow.reset()
        self.ow.write_byte(_SKIP_ROM)
        self.ow.write_byte(_CONVERT)

    def read_temp(self, rom):
        buf = self.buf
        self.ow.reset()
        self.ow.select_rom(rom)
        self.ow.write_byte(_RD_SCRATCHPAD)
        self.ow.readinto(buf)
        if self.ow.crc8(buf):
            raise Exception("CRC error")
        
        # The DS18S20 (0x10) has a different calculation than DS18B20 (0x28)
        # and DS1822 (0x22)
        if rom[0] == 0x10:
            if buf[1]:
                t = buf[0] >> 1 | 0x80
                t = -((~t + 1) & 0xff)
            else:
                t = buf[0] >> 1
            # Apply high-resolution adjustment
            return t - 0.25 + (buf[7] - buf[6]) / buf[7]
        else:
            # DS18B20 and DS1822 share the same calculation
            t = buf[1] << 8 | buf[0]
            if t & 0x8000:  # sign bit set
                t = -((t ^ 0xffff) + 1)
            return t / 16
            
    def write_config(self, rom, config):
        self.config[0] = 0  # Th register
        self.config[1] = 0  # Tl register
        self.config[2] = config  # resolution bits in configuration register
        self.ow.reset()
        self.ow.select_rom(rom)
        self.ow.write_byte(_WR_SCRATCHPAD)
        self.ow.write(self.config)
        
    def read_power_supply(self, rom):
        """
        Returns True if device has external power supply,
        False if device uses parasite power
        """
        self.ow.reset()
        self.ow.select_rom(rom)
        self.ow.write_byte(_RD_POWER_SUPPLY)
        return self.ow.read_bit() == 1