# coding: UTF-8

import smbus
from debug import ERROR, WARN, INFO, DEBUG, TRACE


"""

Grove I2C Mini Motor Driver Class

DataSeet:https://www.seeedstudio.com/Grove-I2C-Mini-Motor-Driver.html

"""


class MiniMotorDriver:
    # @brief コンスタラクタ
    # @detail 初期化処理を行う
    def __init__(self, addr):
        TRACE('MiniMotorDriver generated')
        self._i2c = smbus.SMBus(1)
        self._addr = addr

    def drive(self, speed):
        reg_value = 0x80
        self._i2c.write_byte_data(self._addr, 0x01, 0x80)
        reg_value = abs(int(speed))
        if reg_value > 63:
            reg_value = 63
        reg_value = reg_value << 2
        if speed < 0:
            reg_value |= 0x01
        else:
            reg_value |= 0x02
        self._i2c.write_byte_data(self._addr, 0x00, reg_value)

    def stop(self):
        self._i2c.write_byte_data(self._addr, 0x00, 0x00)

    def brake(self):
        self._i2c.write_byte_data(self._addr, 0x00, 0x03)
