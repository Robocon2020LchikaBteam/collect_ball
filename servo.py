# coding: UTF-8

import time
from debug import ERROR, WARN, INFO, DEBUG, TRACE
import Adafruit_PCA9685


class Servo:
    """

    PCA9685 driver class

    Examples:
        >>> from servo import Servo
        >>> adress = 0x41
        >>> s = Servo(address, 400)
        >>> Servo.write(610, 3, 0.1)

    Attributes:
        _address (int) : slave address
        _pwm (Adafruit_PCA9685.PCA9685) : pwm control class
        _current_pulse_length (int) : pulse length [us?]

    Note:
        set 0 degree : pulse length = 400
        set 90 degree : pulse length = 610

    """

    def __init__(self, address, initial_pulse_length=390):
        TRACE('Servo generated: address = ' + str(address))
        self._address = address
        self._pwm = Adafruit_PCA9685.PCA9685(address=address)
        # Set frequency to 60hz, good for servos.
        self._pwm.set_pwm_freq(60)
        # Set initial pluse length
        self._pwm.set_pwm(0, 0, initial_pulse_length)
        self._current_pulse_length = initial_pulse_length
        self._is_lifting = False

    def write(self, target_pulse_length, duration, diff_t):
        count = int(duration / diff_t)
        for i in range(count):
            self._pwm.set_pwm(0, 0, int(self._current_pulse_length + ((i + 1) * ((target_pulse_length - self._current_pulse_length) / count))))
            time.sleep(diff_t)
        
        self._current_pulse_length = target_pulse_length
    
    def up(self):
        self.write(610, 3, 0.1)
        self._is_lifting = True
    
    def down(self):
        self.write(390, 3, 0.1)
        self._is_lifting = False
    
    def is_lifting(self):
        return self._is_lifting
