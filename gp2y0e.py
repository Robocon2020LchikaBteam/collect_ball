# coding: UTF-8

import smbus
from debug import DEBUG, TRACE, INFO


class Gp2y0e:
    """
    
    GP2Y0E driver class

    Examples:
        >>> from gp2y0e import Gp2y0e
        >>> address = 0x40
        >>> g = Gp2y0e(address)
        >>> print(g.read())
        10.7
    
    Attributes:
        _address (int) : slave address
        _bus (smbus.SMBus) : i2c bus
    
    """

    def __init__(self, address):
        TRACE('Gp2y0e generated: address = ' + str(address))
        self._bus = smbus.SMBus(1)
        self._address = address
    
    def read(self):
        """

        read distance value

        Returns:
            float: distance value [cm]
        
        """
        try:
            data = self._bus.read_i2c_block_data(self._address, 0x5E, 2)
        except:
            return 100
        distance = (data[0] << 4) | data[1]
        distance = distance / 64
        DEBUG('distance = ' + str(distance) + ' [cm]')
        return distance
