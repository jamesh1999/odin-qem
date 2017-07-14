"""TPL0102 - device access class for the TPL0102 dual channel I2C potentiometer

Provides access to control the wiper positions for the TPL0102 device with
helper methods to set potential differences and resistances in potential
divider and rheostat mode respectively.

James Hogge, STFC Application Engineering Group.
"""

from i2c_device import I2CDevice, I2CException

class TPL0102(I2CDevice):
    """TPL0102 class.

    This class implements support to set the resistance across the digital potentiometer
    in rheostat mode or the potential difference at the output in potential divider mode.
    """

    def __init__(self, address=0x50, **kwargs):
        """Initialise the TPL0102 device.
        :param address: The address of the TPL0102 default: 0x50
        """

        I2CDevice.__init__(self, address, **kwargs)

        #Read back current wiper settings
        self.__wiper_pos = [self.readU8(0), self.readU8(1)]
        self.__tot_resistance = 100.0
        self.__low_pd = [0.0,0.0]
        self.__high_pd = [3.3, 3.3]

    def set_total_resistance(self, resistance):
        """Sets the total resistance across the potentiometer for set_resistance()
        :param resistance: Total resistance between H- and L- (Kiloohms)
        """

        self.__tot_resistance = float(resistance)

    def set_resistance(self, wiper, resistance):
        """Sets the resistance of a given wiper in rheostat mode (see datasheet)
        :param wiper: Wiper to set 0=A, 1=B
        :param resistance: Desired resistance between H- and W- (Kiloohms)
        """

        if not wiper in [0,1]:
            raise I2CException("Select either wiper 0 or wiper 1")

        self.__wiper_pos[wiper] = int(resistance / self.__tot_resistance * 256.0)
        self.write8(wiper, self.__wiper_pos[wiper])

    def set_terminal_PDs(self, wiper, low, high):
        """Sets the potential difference for H- and L- on a given wiper for set_PD()
        :param wiper: Wiper to set 0=A, 1=B
        :param low: Low PD (Volts)
        :param high: High PD (Volts)
        """

        if not wiper in [0,1]:
                        raise I2CException("Select either wiper 0 or wiper 1")

        self.__low_pd[wiper] = float(low)
        self.__high_pd[wiper] = float(high)

    def set_PD(self, wiper, pd):
        """Sets the potential difference of a given wiper in potential divider mode (see datasheet)
        :param wiper: Wiper to set 0=A, 1=B
        :param pd: Target potential difference (Volts)
        """

        if not wiper in [0,1]:
            raise I2CException("Select either wiper 0 or wiper 1")

        self.__wiper_pos[wiper] = int((pd - self.__low_pd[wiper]) / (self.__high_pd[wiper] - self.__low_pd[wiper]) * 256.0)
        self.write8(wiper, self.__wiper_pos[wiper])

    def set_wiper(self, wiper, position):
        """Manually sets a wiper position
        :param wiper: Wiper to set 0=A, 1=B
        :param position: Target position [0-255]
        """

        if not wiper in [0,1]:
                        raise I2CException("Select either wiper 0 or wiper 1")

        self.__wiper_pos[wiper] = int(position)
        self.write8(wiper, self.__wiper_pos[wiper])

    def get_wiper(self, wiper):
        """Gets a wiper position
        :param wiper: Wiper to get 0=A, 1=B
        :returns: Current position [0-255]
        """

        if not wiper in [0,1]:
                        raise I2CException("Select either wiper 0 or wiper 1")

        return self.__wiper_pos[wiper]


    def set_non_volatile(self, enable):
        """Sets whether to use non volatile registers on the I2C device
        :param enable: true - non volatile, false - volatile
        """

        dat = self.readU8(16)
        if enable: dat |= 0x80
        else: dat &= ~0x80

        self.write8(16, dat)

    def set_shutdown(self, enable):
        """Sets whether to use shutdown mode
        :param enable: true - device enters shutdown mode, false - normal operation
        """

        dat = self.readU8(16)
        if enable: dat |= 0x40
        else: dat &= ~0x40

        self.write8(16, dat)
