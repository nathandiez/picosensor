import time
from ustruct import unpack, unpack_from
from array import array
 
# BME280 default address.
BME280_I2CADDR = 0x76
 
# Operating Modes
BME280_OSAMPLE_1 = 1
BME280_OSAMPLE_2 = 2
BME280_OSAMPLE_4 = 3
BME280_OSAMPLE_8 = 4
BME280_OSAMPLE_16 = 5
 
BME280_REGISTER_CONTROL_HUM = 0xF2
BME280_REGISTER_CONTROL = 0xF4
 
class BME280:
 
    def __init__(self, mode=BME280_OSAMPLE_1, address=BME280_I2CADDR, i2c=None, **kwargs):
        self._mode = 1
        self.address = address
        self.i2c = i2c
 
        dig_88_a1 = self.i2c.readfrom_mem(self.address, 0x88, 26) # load calibration data
        dig_e1_e7 = self.i2c.readfrom_mem(self.address, 0xE1, 7)
        self.dig_T1, self.dig_T2, self.dig_T3, self.dig_P1, \
            self.dig_P2, self.dig_P3, self.dig_P4, self.dig_P5, \
            self.dig_P6, self.dig_P7, self.dig_P8, self.dig_P9, \
            _, self.dig_H1 = unpack("<HhhHhhhhhhhhBB", dig_88_a1)
 
        self.dig_H2, self.dig_H3 = unpack("<hB", dig_e1_e7)
        e4_sign = unpack_from("<b", dig_e1_e7, 3)[0]
        self.dig_H4 = (e4_sign << 4) | (dig_e1_e7[4] & 0xF)
        e6_sign = unpack_from("<b", dig_e1_e7, 5)[0]
        self.dig_H5 = (e6_sign << 4) | (dig_e1_e7[4] >> 4)
        self.dig_H6 = unpack_from("<b", dig_e1_e7, 6)[0]
        self.i2c.writeto_mem(self.address, BME280_REGISTER_CONTROL, bytearray([0x3F]))
        self.t_fine = 0
        self._l1_barray = bytearray(1)
        self._l8_barray = bytearray(8)
        self._l3_resultarray = array("i", [0, 0, 0])
 
    def read_raw_data(self, result):
        self._l1_barray[0] = self._mode
        self.i2c.writeto_mem(self.address, BME280_REGISTER_CONTROL_HUM, self._l1_barray)
        self._l1_barray[0] = self._mode << 5 | self._mode << 2 | 1
        self.i2c.writeto_mem(self.address, BME280_REGISTER_CONTROL, self._l1_barray)
 
        sleep_time = 1250 + 2300 * (1 << self._mode)
        sleep_time = sleep_time + 2300 * (1 << self._mode) + 575
        sleep_time = sleep_time + 2300 * (1 << self._mode) + 575
        time.sleep_us(sleep_time)
 
        self.i2c.readfrom_mem_into(self.address, 0xF7, self._l8_barray)
        readout = self._l8_barray
        raw_press = ((readout[0] << 16) | (readout[1] << 8) | readout[2]) >> 4
        raw_temp = ((readout[3] << 16) | (readout[4] << 8) | readout[5]) >> 4
        raw_hum = (readout[6] << 8) | readout[7]
        result[0] = raw_temp
        result[1] = raw_press
        result[2] = raw_hum
 
    def read_compensated_data(self, result=None):
        self.read_raw_data(self._l3_resultarray)
        raw_temp, raw_press, raw_hum = self._l3_resultarray
 
        var1 = ((raw_temp >> 3) - (self.dig_T1 << 1)) * (self.dig_T2 >> 11)
        var2 = (((((raw_temp >> 4) - self.dig_T1) *
                  ((raw_temp >> 4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
        self.t_fine = var1 + var2
        temp = (self.t_fine * 5 + 128) >> 8
 
        var1 = self.t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = (((var1 * var1 * self.dig_P3) >> 8) + ((var1 * self.dig_P2) << 12))
        var1 = (((1 << 47) + var1) * self.dig_P1) >> 33
        if var1 == 0:
            pressure = 0
        else:
            p = 1048576 - raw_press
            p = (((p << 31) - var2) * 3125) // var1
            var1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
            var2 = (self.dig_P8 * p) >> 19
            pressure = ((p + var1 + var2) >> 8) + (self.dig_P7 << 4)
 
        h = self.t_fine - 76800
        h = (((((raw_hum << 14) - (self.dig_H4 << 20) - (self.dig_H5 * h)) + 16384) >> 15) *
             (((((((h * self.dig_H6) >> 10) * (((h * self.dig_H3) >> 11) + 32768)) >> 10) +
                2097152) * self.dig_H2 + 8192) >> 14))
        h = h - (((((h >> 15) * (h >> 15)) >> 7) * self.dig_H1) >> 4)
        h = 0 if h < 0 else h
        h = 419430400 if h > 419430400 else h
        humidity = h >> 12
 
        if result:
            result[0] = temp
            result[1] = pressure
            result[2] = humidity
            return result
 
        return array("i", (temp, pressure, humidity))
 
    @property
    def values(self):
        t, p, h = self.read_compensated_data()
        p = p // 256
        pi = p // 100
        pd = p - pi * 100
        hi = h // 1024
        hd = h * 100 // 1024 - hi * 100
        t = t/100*9/5+32
        h = h/1024
        p = p/100*0.02952998307
        return (t, h, p)
