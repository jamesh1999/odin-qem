"""AD7998 - device access class for the AD7998 12-bit I2C ADC.

This class implements support for the AD7998 I2C ADC device, providing simple
methods to convert and read in input channel.

James Hogge, STFC Application Engineering Group.
"""

from i2c_device import I2CDevice, I2CException


class AD7998(I2CDevice):
    """AD7998 class.

    This class impleents support for the AD7998 I2C ADC device, allowing input
    channel conversions to be triggered and read.
    """

    NUM_ADC_CHANNELS = 8

    def __init__(self, address=0x20, **kwargs):
        """Initialise the AD7998 device.

        :param address: address of the AD7998 device on the I2C bus
        :param kwargs: keyword arguments to be passed to the underlying I2CDevice
        """
        # Initialise the I2CDevice superclass instance
        I2CDevice.__init__(self, address, **kwargs)

        # Set cycle register to fastest conversion mode
        self.write8(3, 1)

    def read_input_raw(self, channel):
        """Convert and read a raw ADC value on a channel.

        This method triggers a conversion on the specified channel and
        reads back the raw 16-bit value from the device

        :param channel: channel to convert
        :return raw conversion result
        """
        # Check legal channel requested
        if channel < 0 or channel >= self.NUM_ADC_CHANNELS:
            raise I2CException("Illegal channel {} requested".format(channel))

        # Trigger a conversion on channel, setting upper 4 bits of address pointer
        self.write8(0x70 + ((channel + 1) << 4), 0)

        # Read conversion register
        data = self.readU16(0)

        # Swap bytes to correct order
        data = ((data & 0xff) << 8) + ((data & 0xff00) >> 8)

        return data

    def read_input_scaled(self, channel):
        """Convert and read a scaled valye on a channel.

        This method triggers a conversion on the specified channel and
        returns the value as a fraction of the full scale i.e between
        values of 0.0 and 1.0

        :param channel: channel to convert
        :return scaled conversion result
        """
        # Trigger conversion and read raw value
        data = self.read_input_raw(channel)

        # Mask off channel identifier
        data &= 0xfff

        # Return scaled value
        return data / 4095.0
