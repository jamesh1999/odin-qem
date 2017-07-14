"""AD5321 - device access class for the AD5321 12-bit I2C DAC.

This class implements support for the AD5321 I2C DAC device, providing simple
methods to set the output value (as a fraction of full-scale) and to read the
scaled setting back.

James Hogge, STFC Application Engineering Group.
"""

from lpdpower.i2c_device import I2CDevice, I2CException


class AD5321(I2CDevice):
    """AD5321 class.

    This class implements support for the AD5321 I2C device, allowing the output voltage of the
    DAC to be set and read back.
    """

    def __init__(self, address=0xc, **kwargs):
        """Initialise the AD5321 device.

        :param address: address of the AD5321 on the I2C bus
        :param kwargs: keyword arguments to be passed to the underlying I2CDevice
        """
        # Initialise the I2CDevice superclass instance
        I2CDevice.__init__(self, address, **kwargs)

    def set_output_scaled(self, value):
        """Set the output voltage of the DAC.

        This method sets the output voltage of the DAC, specified as a fraction of the
        full scale, i.e between values of 0.0 and 1.0.

        :param value: output voltage value (0.0-1.0)
        """
        # Check a legal output value has been specified
        if value < 0.0 or value > 1.0:
            raise I2CException("Illegal output value {} specified".format(value))

        # Convert the value to ADUs
        value = int(value * 4096)
        if value == 4096:
            value = 4095

        # Extract the MSB and LSB
        msb = (value & 0xFF00) >> 8
        lsb = (value & 0xFF)

        # Write values to device
        self.write8(msb, lsb)

    def read_value_scaled(self):
        """Read the current output value set in the device.

        The method reads the current value set in the device, returning the value
        as a fraction of the full scale.

        :return current output seting as fraction of full scale.
        """
        # Read the value
        value = self.readU16(0)

        # Reverse bytes
        value = ((value & 0xff00) >> 8) + ((value & 0xff) << 8)

        # Return scaled value
        return value / 4096.0
