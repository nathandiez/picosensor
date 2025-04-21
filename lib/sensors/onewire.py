# MicroPython 1-Wire driver
# MIT license; Copyright (c) 2016 Damien P. George

import machine
import time
from micropython import const

_SEARCH_ROM = const(0xf0)
_MATCH_ROM = const(0x55)
_SKIP_ROM = const(0xcc)
_SEARCH_ALARM = const(0xec)

class OneWireError(Exception):
    pass

class OneWire:
    def __init__(self, pin):
        self.pin = pin
        self.pin.init(pin.OUT, pull=None)
        # Perform a device reset to start fresh
        self.reset()

    def reset(self):
        """
        Reset the 1-Wire bus
        Returns True if at least one device responds with a presence pulse
        """
        sleep_us = time.sleep_us
        disable_irq = machine.disable_irq
        enable_irq = machine.enable_irq
        pin = self.pin

        # Ensure line is high for at least 1µs
        pin.init(pin.OUT, pull=None)
        pin.value(1)
        sleep_us(1)
        
        # Reset pulse (bring low for at least 480µs)
        irq_state = disable_irq()
        pin.value(0)
        sleep_us(480)
        
        # Release line and wait for devices to pull low (presence pulse)
        pin.init(pin.IN, pull=None)
        sleep_us(70)
        
        # Get line value and wait until end of presence pulse
        val = pin.value()
        enable_irq(irq_state)
        sleep_us(410)
        
        # A device responded if the line was pulled low
        return val == 0

    def read_bit(self):
        """Read a single bit from the 1-Wire bus"""
        sleep_us = time.sleep_us
        disable_irq = machine.disable_irq
        enable_irq = machine.enable_irq
        pin = self.pin

        irq_state = disable_irq()
        pin.init(pin.OUT, pull=None)
        pin.value(0)
        sleep_us(1)  # Pull low for at least 1µs
        
        # Release line and let devices drive the bus
        pin.init(pin.IN, pull=None)
        sleep_us(10)  # Wait for device to respond
        
        # Sample the bit value from the line
        val = pin.value()
        enable_irq(irq_state)
        sleep_us(50)  # Recovery time
        
        return val

    def write_bit(self, value):
        """Write a single bit to the 1-Wire bus"""
        sleep_us = time.sleep_us
        disable_irq = machine.disable_irq
        enable_irq = machine.enable_irq
        pin = self.pin

        irq_state = disable_irq()
        pin.init(pin.OUT, pull=None)
        pin.value(0)
        
        # Timing depends on the bit value
        sleep_us(1)  # Pull low for at least 1µs
        
        # Set line to bit value
        if value:
            pin.value(1)
            
        sleep_us(60)  # Hold value for required time
        
        # Release line
        pin.value(1)
        enable_irq(irq_state)
        sleep_us(1)  # Recovery time

    def write_byte(self, value):
        """Write a byte (8 bits) to the 1-Wire bus"""
        for i in range(8):
            self.write_bit(value & 1)
            value >>= 1

    def read_byte(self):
        """Read a byte (8 bits) from the 1-Wire bus"""
        value = 0
        for i in range(8):
            value |= self.read_bit() << i
        return value

    def readinto(self, buf):
        """Read bytes from the 1-Wire bus into the buffer 'buf'"""
        for i in range(len(buf)):
            buf[i] = self.read_byte()

    def write(self, buf):
        """Write bytes from the buffer 'buf' to the 1-Wire bus"""
        for b in buf:
            self.write_byte(b)

    def select_rom(self, rom):
        """Select a specific device on the 1-Wire bus using its ROM code"""
        self.reset()
        self.write_byte(_MATCH_ROM)
        self.write(rom)

    def scan(self):
        """Scan the 1-Wire bus and return a list of ROM codes for devices found"""
        devices = []
        self._search_rom(devices, 0)
        return devices

    def _search_rom(self, devices, l_bit):
        """Perform the ROM search algorithm to discover all devices on the bus"""
        if self.reset() == 0:
            return
        
        rom = bytearray(8)
        bit_index = 1
        conflict_index = 0
        
        self.write_byte(_SEARCH_ROM)
        
        for byte_index in range(8):
            rom_byte = 0
            for bit_index in range(8):
                # Read the bit and its complement
                id_bit = self.read_bit()
                cmp_id_bit = self.read_bit()
                
                # Check for no devices on the bus
                if id_bit == 1 and cmp_id_bit == 1:
                    return
                
                # Path decision based on the bit read
                if id_bit != cmp_id_bit:
                    # No conflict, follow the detected bit
                    dir_bit = id_bit
                else:
                    # We have a conflict, use path selector
                    bit_number = byte_index * 8 + bit_index
                    if bit_number < l_bit:
                        # Use the same bit as before
                        dir_bit = (rom[byte_index] >> bit_index) & 1
                    elif bit_number == l_bit:
                        # We're at the decision point, take the 1 branch
                        dir_bit = 1
                        conflict_index = bit_number
                    else:
                        # Take the 0 branch if not yet at the decision point
                        dir_bit = 0
                        conflict_index = bit_number
                
                # Set the bit in the ROM byte
                if dir_bit:
                    rom_byte |= 1 << bit_index
                
                # Write the chosen direction
                self.write_bit(dir_bit)
            
            rom[byte_index] = rom_byte
        
        # We've found a device
        devices.append(bytes(rom))
        
        # Search for more devices down the 0 path if we had conflicts
        if conflict_index:
            self._search_rom(devices, conflict_index)

    def crc8(self, data):
        """Compute CRC-8 of the provided data using the 1-Wire polynomial"""
        crc = 0
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x01:
                    crc = (crc >> 1) ^ 0x8C
                else:
                    crc >>= 1
        return crc