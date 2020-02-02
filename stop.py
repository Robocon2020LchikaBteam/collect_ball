# coding: UTF-8

from miniMotorDriver import MiniMotorDriver

"""

stop motors

"""

if __name__ == '__main__':
    left_motor = MiniMotorDriver(0x60)
    right_motor = MiniMotorDriver(0x65)
    left_motor.stop()
    right_motor.stop()
